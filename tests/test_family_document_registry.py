"""Behavioral tests for the bounded family document registry, not packaging mirrors."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PAYLOAD = Path(os.environ.get("FAMILY_REGISTRY_PAYLOAD", Path(__file__).resolve().parents[1] / "plugins/family-document-registry/family-document-registry"))
SPEC = importlib.util.spec_from_file_location("tested_family_registry", PAYLOAD / "runtime/registry.py")
CORE = importlib.util.module_from_spec(SPEC)
prior = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(CORE)
finally:
    sys.dont_write_bytecode = prior


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="family-doc-test-")
        self.root = Path(self.temp.name).resolve() / "公开虚构材料"
        shutil.copytree(PAYLOAD / "examples", self.root)
        self.catalog = self.root / "家庭台账-初始.json"
        self.plan = self.root / "材料计划-完整.json"
        self.output = self.root / "材料副本"
        self.initial_hashes = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in self.root.rglob("*") if p.is_file()}

    def tearDown(self):
        self.temp.cleanup()

    def call(self, op, **values):
        return CORE.dispatch(op, {"workspace": str(self.root), **values})

    def error(self, result, code):
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["error"]["code"], code, result)
        self.assertRegex(result["error"]["message"], r"[\u4e00-\u9fff]")

    def inspect(self, path=None):
        return self.call("manage", action="inspect", catalog_path=str(path or self.catalog))

    def initialize(self):
        preview = self.inspect()
        self.assertTrue(preview["ok"], preview)
        saved = self.call("manage", action="init", catalog_path=str(self.catalog), confirmed=True,
                          expected_revision=0, expected_preview_sha256=preview["preview_sha256"])
        self.assertTrue(saved["ok"], saved)
        return saved

    def preview(self, path=None, output=None):
        return self.call("pack", plan_path=str(path or self.plan), output_dir=str(output or self.output))

    def build(self, preview, **extra):
        return self.call("pack", plan_path=str(self.plan), output_dir=str(self.output), mode="build", confirmed=True,
                         expected_revision=preview["revision"], expected_preview_sha256=preview["preview_sha256"], **extra)

    def change_catalog(self, mutator, name="修改.json"):
        c = json.loads(self.catalog.read_text())
        mutator(c)
        path = self.root / name
        path.write_text(json.dumps(c, ensure_ascii=False))
        return path

    def test_status_does_not_initialize(self):
        s = self.call("manage")
        self.assertTrue(s["ok"])
        self.assertFalse(s["initialized"])
        self.assertEqual(s["revision"], 0)
        self.assertFalse((self.root / CORE.STATE).exists())

    def test_inspect_complete_metadata_without_writes(self):
        p = self.inspect()
        self.assertTrue(p["ok"])
        self.assertEqual(len(p["catalog"]["people"]), 2)
        self.assertEqual(len(p["catalog"]["documents"]), 6)
        self.assertEqual(p["files"]["unattached"]["status"], "unattached")
        raw = (self.root / "资料/林晨-新护照.txt").read_bytes()
        self.assertEqual(p["files"]["passport_new"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("公开虚构测试附件", json.dumps(p, ensure_ascii=False))
        self.assertFalse((self.root / CORE.STATE).exists())

    def test_init_requires_confirmation_without_side_effect(self):
        self.error(self.call("manage", action="init", catalog_path=str(self.catalog), confirmed=False), "confirmation_required")
        self.assertFalse((self.root / CORE.STATE).exists())

    def test_wrong_registration_preview_has_no_state(self):
        self.error(self.call("manage", action="init", catalog_path=str(self.catalog), confirmed=True,
                             expected_revision=0, expected_preview_sha256="0" * 64), "preview_changed")
        self.assertFalse((self.root / CORE.STATE).exists())

    def test_init_status_and_private_permissions(self):
        saved = self.initialize()
        s = self.call("manage", action="status")
        self.assertEqual(s["revision"], 1)
        self.assertEqual(s["registry_sha256"], saved["registry_sha256"])
        self.assertEqual(s["catalog"], json.loads(self.catalog.read_text()))
        for p in (self.root / CORE.STATE).iterdir():
            self.assertEqual(p.stat().st_mode & 0o077, 0)
        self.assertEqual((self.root / CORE.STATE).stat().st_mode & 0o077, 0)

    def test_restart_in_fresh_process_reads_exact_revision(self):
        s = self.initialize()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, "-B", str(PAYLOAD / "runtime/registry.py"), "manage", "--input-json",
                              json.dumps({"workspace": str(self.root), "action": "status"})], capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["registry_sha256"], s["registry_sha256"])

    def test_calendar_month_end_and_leap_year(self):
        for before, offset, after in [(date(2026,10,31),1,date(2026,11,30)), (date(2026,10,31),-1,date(2026,9,30)),
                                      (date(2024,2,29),12,date(2025,2,28)), (date(2024,1,31),1,date(2024,2,29)),
                                      (date(2026,3,15),1,date(2026,4,15)), (date(2026,12,31),1,date(2027,1,31))]:
            self.assertEqual(CORE.add_months(before, offset), after)

    def test_expiry_inclusive_boundary_and_precision(self):
        self.initialize()
        r = self.call("report", reference_date="2026-10-31", horizon_months=1)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["horizon_date"], "2026-11-30")
        docs = {d["id"]: d for d in r["documents"]}
        self.assertEqual(docs["passport_old"]["expiry_state"], "expired")
        self.assertEqual(docs["passport_old"]["status"], "renewing")
        self.assertEqual(docs["permit_unknown"]["expiry_state"], "unknown")
        self.assertEqual(docs["certificate_month"]["expiry_state"], "month_precision")
        self.assertEqual(docs["passport_new"]["replaced_by"], [])
        d = docs["passport_new"]
        self.assertEqual(CORE.expiry_state(d, date(2027,3,31), date(2027,4,30))[0], "expires_today")
        self.assertEqual(CORE.expiry_state(d, date(2027,3,30), date(2027,3,31))[0], "expiring")

    def test_filters_are_exact_and_read_only(self):
        self.initialize()
        before = self.call("manage", action="status")
        r = self.call("report", reference_date="2026-10-31", person_id="p_mei", kind="学习证明")
        self.assertEqual([x["id"] for x in r["documents"]], ["certificate_month"])
        self.assertEqual(self.call("manage", action="status")["registry_sha256"], before["registry_sha256"])
        self.error(self.call("report", reference_date="2026-10-31", person_id="nonexistent"), "invalid_reference")

    def test_unknown_does_not_infer_replacement(self):
        c = self.change_catalog(lambda c: c["documents"][1].update(expires_on=None))
        p = self.inspect(c)
        self.assertTrue(p["ok"])
        saved = self.call("manage", action="init", catalog_path=str(c), confirmed=True,
                          expected_revision=0, expected_preview_sha256=p["preview_sha256"])
        self.assertTrue(saved["ok"])
        r = self.call("report", reference_date="2026-10-31")
        old = next(x for x in r["documents"] if x["id"] == "passport_old")
        self.assertEqual(old["status"], "renewing")
        self.assertEqual(old["replaced_by"], [])

    def test_update_keeps_history_and_explicit_replacement(self):
        old = self.initialize()
        c = self.root / "家庭台账-确认替换.json"
        p = self.inspect(c)
        s = self.call("manage", action="update", catalog_path=str(c), confirmed=True,
                      expected_revision=1, expected_preview_sha256=p["preview_sha256"])
        self.assertTrue(s["ok"], s)
        self.assertEqual(s["revision"], 2)
        self.assertEqual(s["previous_registry_sha256"], old["registry_sha256"])
        self.assertTrue((self.root / CORE.STATE / ("001-"+old["registry_sha256"]+".json")).is_file())
        d = next(x for x in self.call("report", reference_date="2026-10-31")["documents"] if x["id"] == "passport_old")
        self.assertEqual(d["replaced_by"], ["passport_new"])
        self.assertEqual(d["status"], "archived")

    def test_stale_revision_does_not_modify_head(self):
        old = self.initialize(); p = self.inspect()
        self.error(self.call("manage", action="update", catalog_path=str(self.catalog), confirmed=True,
                             expected_revision=0, expected_preview_sha256=p["preview_sha256"]), "revision_conflict")
        self.assertEqual(self.call("manage", action="status")["registry_sha256"], old["registry_sha256"])

    def test_catalog_deletion_is_rejected(self):
        self.initialize()
        c = self.change_catalog(lambda c: c["documents"].pop())
        p = self.inspect(c)
        self.error(self.call("manage", action="update", catalog_path=str(c), confirmed=True,
                             expected_revision=1, expected_preview_sha256=p["preview_sha256"]), "history_required")

    def test_existing_id_identity_cannot_be_reused(self):
        self.initialize()
        c = self.change_catalog(lambda c: c["documents"][0].update(person_id="p_mei"))
        p = self.inspect(c)
        self.error(self.call("manage", action="update", catalog_path=str(c), confirmed=True,
                             expected_revision=1, expected_preview_sha256=p["preview_sha256"]), "identity_conflict")

    def test_duplicate_keys_and_invalid_dates(self):
        self.error(self.inspect(self.root / "重复键.json"), "duplicate_json_key")
        self.error(self.inspect(self.root / "非法日期.json"), "invalid_date")
        for bad in ("2025-02-29", "2026-13", "明年", "2026-2-01", "0000-01-01"):
            path = self.change_catalog(lambda c: c["documents"][0].update(expires_on=bad))
            self.error(self.inspect(path), "invalid_date")

    def test_unknown_fields_duplicate_ids_and_invalid_status(self):
        for mutate, code in [(lambda c: c.update(ignored=True), "invalid_schema"),
                             (lambda c: c["people"].append(c["people"][0]), "duplicate_id"),
                             (lambda c: c["documents"].append(c["documents"][0]), "duplicate_id"),
                             (lambda c: c["documents"][0].update(status="guessed"), "invalid_schema")]:
            self.error(self.inspect(self.change_catalog(mutate)), code)

    def test_invalid_reference_and_replacement_cycle(self):
        for mutate in (lambda c: c["documents"][0].update(replaces="missing"),
                       lambda c: c["documents"][0].update(replaces="permit_unknown")):
            self.error(self.inspect(self.change_catalog(mutate)), "invalid_reference")
        def cycle(c):
            c["documents"][0]["replaces"]="passport_new"
            c["documents"][1]["replaces"]="passport_old"
        self.error(self.inspect(self.change_catalog(cycle)), "invalid_reference")

    def test_input_limits_and_booleans(self):
        self.error(self.inspect(self.change_catalog(lambda c: c["people"].extend([{"id":"x"+str(i),"name":"虚构"} for i in range(32)]))), "size_limit")
        self.initialize()
        self.error(self.call("report", reference_date="2026-10-31", horizon_months=True), "invalid_argument")
        path = self.root / "巨大.json"; path.write_bytes(b" " * (CORE.MAX_JSON+1))
        self.error(self.inspect(path), "size_limit")

    def test_source_hash_change_invalidates_registration(self):
        p = self.inspect()
        (self.root / "资料/林晨-新护照.txt").write_text("另一个公开虚构内容")
        self.error(self.call("manage", action="init", catalog_path=str(self.catalog), confirmed=True,
                             expected_revision=0, expected_preview_sha256=p["preview_sha256"]), "preview_changed")
        self.assertFalse((self.root / CORE.STATE).exists())

    def test_catalog_text_change_invalidates_registration(self):
        p = self.inspect(); self.catalog.write_text(self.catalog.read_text()+" ")
        self.error(self.call("manage", action="init", catalog_path=str(self.catalog), confirmed=True,
                             expected_revision=0, expected_preview_sha256=p["preview_sha256"]), "preview_changed")

    def test_missing_files_recorded_without_false_present(self):
        (self.root / "资料/林晨-旧护照.txt").unlink()
        p = self.inspect(); self.assertEqual(p["files"]["passport_old"]["status"], "missing")
        self.initialize()
        r = self.call("report", reference_date="2026-10-31")
        self.assertEqual(next(d for d in r["documents"] if d["id"]=="passport_old")["file_status"], "missing")

    def test_reports_changed_files_but_does_not_adopt(self):
        self.initialize()
        (self.root / "资料/林晨-新护照.txt").write_text("公开虚构变更")
        r = self.call("report", reference_date="2026-10-31")
        d = next(d for d in r["documents"] if d["id"]=="passport_new")
        self.assertEqual(d["file_status"], "changed")
        self.assertNotEqual(d["actual_sha256"], d["registered_sha256"])
        self.error(self.preview(), "source_changed")

    def test_file_growth_limit(self):
        (self.root / "资料/林晨-新护照.txt").write_bytes(b"x" * (CORE.MAX_FILE+1))
        self.error(self.inspect(), "size_limit")

    def test_outside_workspace_and_dot_paths_rejected(self):
        self.error(self.inspect(Path(self.temp.name) / "outside.json"), "outside_workspace")
        self.error(self.call("manage", action="inspect", catalog_path=str(self.root)+"/../outside.json"), "unsafe_path")
        for path in ("../outside.txt", "/tmp/out.txt", ".family-document-registry/HEAD.json", "资料//x", "资料/./x"):
            self.error(self.inspect(self.change_catalog(lambda c: c["documents"][0].update(path=path))), "unsafe_path")

    def test_symlink_and_hardlink_sources_are_rejected(self):
        target=self.root/"资料/林晨-新护照.txt"; backup=target.read_bytes(); target.unlink()
        target.symlink_to(self.root/"资料/林晨-旧护照.txt")
        self.error(self.inspect(), "filesystem_error")
        target.unlink(); os.link(self.root/"资料/林晨-旧护照.txt",target)
        self.error(self.inspect(), "unsafe_file")

    def test_symlink_workspace_parent_rejected(self):
        link=Path(self.temp.name)/"link"; link.symlink_to(self.root,target_is_directory=True)
        self.error(CORE.dispatch("manage",{"workspace":str(link),"action":"status"}), "filesystem_error")

    def test_registry_integrity_failure(self):
        s=self.initialize(); path=self.root/CORE.STATE/("001-"+s["registry_sha256"]+".json")
        path.write_bytes(path.read_bytes()+b" ")
        self.error(self.call("manage",action="status"), "integrity_mismatch")

    def test_store_permissions_and_link(self):
        self.initialize(); (self.root/CORE.STATE).chmod(0o755)
        self.error(self.call("manage"), "invalid_registry")

    def test_pack_without_registry_is_rejected(self):
        self.error(self.preview(), "registry_missing")

    def test_pack_preview_date_boundaries_without_writes(self):
        self.initialize(); p=self.preview()
        self.assertTrue(p["ok"],p);self.assertTrue(p["complete"],p)
        self.assertEqual(p["copy_count"],2)
        self.assertTrue(all(not x["issues"] for x in p["items"]))
        self.assertFalse(p["writes_performed"]); self.assertFalse(self.output.exists())

    def test_pack_creation_exact_bytes_and_chinese_checklist(self):
        self.initialize(); p=self.preview(); result=self.build(p)
        self.assertTrue(result["ok"],result)
        manifest=(self.output/"manifest.json").read_bytes()
        self.assertEqual(hashlib.sha256(manifest).hexdigest(),result["manifest_sha256"])
        m=json.loads(manifest)
        self.assertEqual(m["preview_sha256"],p["preview_sha256"])
        for item in p["items"]:
            self.assertEqual((self.output/item["output_file"]).read_bytes(),(self.root/item["source"]).read_bytes())
            self.assertTrue(item["output_file"].endswith(".txt"))
        self.assertIn("家庭文档材料包",(self.output/"checklist.md").read_text())
        for name,h in self.initial_hashes.items():
            self.assertEqual(hashlib.sha256((self.root/name).read_bytes()).hexdigest(),h)

    def test_pack_missing_and_uncertain_is_not_complete(self):
        self.initialize(); p=self.preview(self.root/"材料计划-待确认.json")
        self.assertTrue(p["ok"],p);self.assertFalse(p["complete"])
        self.assertIn("expiry_uncertain",p["items"][2]["issues"])
        self.assertIn("missing_document",p["items"][3]["issues"])
        r=self.call("pack",plan_path=str(self.root/"材料计划-待确认.json"),output_dir=str(self.output),mode="build",confirmed=True,
                    expected_revision=p["revision"],expected_preview_sha256=p["preview_sha256"])
        self.assertTrue(r["ok"],r);self.assertFalse(r["complete"])
        self.assertIn("到期日期不确定",(self.output/"checklist.md").read_text())

    def test_pack_confirmation_and_wrong_hash_refused(self):
        self.initialize();p=self.preview()
        self.error(self.call("pack",plan_path=str(self.plan),output_dir=str(self.output),mode="build",confirmed=False),"confirmation_required")
        self.error(self.call("pack",plan_path=str(self.plan),output_dir=str(self.output),mode="build",confirmed=True,
                             expected_revision=1,expected_preview_sha256="0"*64),"preview_changed")
        self.assertFalse(self.output.exists())

    def test_existing_empty_directory_and_repeat_output_refused(self):
        self.initialize();p=self.preview();self.assertTrue(self.build(p)["ok"])
        before=(self.output/"manifest.json").read_bytes();self.error(self.build(p),"output_exists")
        self.assertEqual((self.output/"manifest.json").read_bytes(),before)
        existing=self.root/"旧空目录";existing.mkdir()
        self.error(self.preview(output=existing),"output_exists")

    def test_changed_plan_refused_before_creation(self):
        self.initialize();p=self.preview();plan=json.loads(self.plan.read_text());plan["requirements"][0]["label"]="用户变更要求"
        self.plan.write_text(json.dumps(plan,ensure_ascii=False))
        self.error(self.build(p),"preview_changed");self.assertFalse(self.output.exists())

    def test_changed_output_refused(self):
        self.initialize();p=self.preview()
        self.error(self.call("pack",plan_path=str(self.plan),output_dir=str(self.root/"另一个输出"),mode="build",confirmed=True,
                             expected_revision=1,expected_preview_sha256=p["preview_sha256"]),"preview_changed")

    def test_changed_source_refused_before_creation(self):
        self.initialize();p=self.preview();(self.root/"资料/林晨-新护照.txt").write_text("已变化的公开虚构文件")
        self.error(self.build(p),"source_changed");self.assertFalse(self.output.exists())

    def test_stale_pack_registry_revision_refused(self):
        self.initialize();p=self.preview();c=self.root/"家庭台账-确认替换.json";cpreview=self.inspect(c)
        self.call("manage",action="update",catalog_path=str(c),confirmed=True,expected_revision=1,expected_preview_sha256=cpreview["preview_sha256"])
        self.error(self.build(p),"revision_conflict");self.assertFalse(self.output.exists())

    def test_missing_selected_source_refused(self):
        self.initialize();(self.root/"资料/林晨-新护照.txt").unlink()
        self.error(self.preview(),"source_missing")

    def test_plan_foreign_person_and_duplicate_item_rejected(self):
        self.initialize();plan=json.loads(self.plan.read_text());plan["requirements"][0]["person_id"]="p_mei"
        self.plan.write_text(json.dumps(plan));self.error(self.preview(),"invalid_reference")
        plan=json.loads((PAYLOAD/"examples/材料计划-完整.json").read_text());plan["requirements"].append(plan["requirements"][0])
        self.plan.write_text(json.dumps(plan));self.error(self.preview(),"duplicate_id")

    def test_html_in_label_is_escaped_as_data(self):
        self.initialize();plan=json.loads(self.plan.read_text());plan["requirements"][0]["label"]='<script>不要执行</script>|'
        self.plan.write_text(json.dumps(plan,ensure_ascii=False));p=self.preview();self.assertTrue(self.build(p)["ok"])
        text=(self.output/"checklist.md").read_text();self.assertIn('&lt;script&gt;',text);self.assertNotIn('<script>',text)

    def test_partial_output_is_explicit_and_originals_preserved(self):
        self.initialize();p=self.preview();original=CORE.write_new
        def disk_full(fd,name,raw):
            if name=='manifest.json':raise OSError("simulated write error")
            return original(fd,name,raw)
        with mock.patch.object(CORE,'write_new',side_effect=disk_full):r=self.build(p)
        self.error(r,'partial_output');self.assertTrue(self.output.exists());self.assertFalse((self.output/'manifest.json').exists())
        self.assertEqual(set(self.initial_hashes),{x for x in self.initial_hashes if (self.root/x).exists()})

    def test_legitimate_concurrent_updates_never_lose_revision(self):
        self.initialize();p=self.inspect()
        def save():return self.call('manage',action='update',catalog_path=str(self.catalog),confirmed=True,expected_revision=1,expected_preview_sha256=p['preview_sha256'])
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:save(),range(2)))
        self.assertEqual(sum(r['ok'] for r in results),1,results)
        self.assertIn(next(r['error']['code'] for r in results if not r['ok']),('registry_busy','revision_conflict'))
        self.assertEqual(self.call('manage')['revision'],2)

    def test_core_has_no_network_attempts(self):
        with mock.patch('socket.socket',side_effect=AssertionError('network not authorized')):
            self.initialize();self.assertTrue(self.call('report',reference_date='2026-10-31')['ok'])
            p=self.preview();self.assertTrue(self.build(p)['ok'])

    def test_cli_chinese_help_and_refusal_exit_code(self):
        run=subprocess.run([sys.executable,'-B',str(PAYLOAD/'runtime/registry.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0);self.assertIn('家庭文档台账',run.stdout)
        run=subprocess.run([sys.executable,'-B',str(PAYLOAD/'runtime/registry.py'),'report','--input-json',json.dumps({'workspace':str(self.root),'reference_date':'2026-10-31'})],capture_output=True,text=True)
        self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['error']['code'],'registry_missing')

    def test_real_openjiuwen_sdk_end_to_end(self):
        # Keep the SDK's lazy module __getattr__ hooks out of other tests'
        # warnings-registry discovery. Exercise the real SDK in a fresh process.
        if os.environ.get('FAMILY_SDK_CHILD') != '1':
            if importlib.util.find_spec('openjiuwen') is None:
                self.skipTest('Optional host SDK is not installed in this test environment')
            child = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                                    'RegistryTests.test_real_openjiuwen_sdk_end_to_end'],
                                   env=dict(os.environ, FAMILY_SDK_CHILD='1', PYTHONDONTWRITEBYTECODE='1'),
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(child.returncode, 0, child.stdout+'\n'+child.stderr)
            if 'skipped=1' in child.stderr:
                self.skipTest('Optional host SDK dependencies are unavailable in the child process')
            return
        try:
            from openjiuwen.core.foundation.tool import Tool
        except ImportError:
            self.skipTest('Optional host SDK is not installed in this test environment')
        spec=importlib.util.spec_from_file_location('tested_family_registry_tools',PAYLOAD/'tools/registry_tools.py')
        module=importlib.util.module_from_spec(spec)
        old=sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode=True;spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode=old
        actual=[]
        async def exercise():
            manage,report,pack=module.ManageFamilyRegistryTool(),module.InspectFamilyDocumentsTool(),module.PrepareFamilyDocumentPackTool()
            self.assertTrue(all(isinstance(t,Tool) for t in (manage,report,pack)))
            async def invoke(t,**p):
                result=await t.invoke({'workspace':str(self.root),**p})
                actual.append({'class':t.__class__.__name__,'parameters':p,'result':result})
                self.assertEqual(result['version'],'1.0.0');return result
            status=await invoke(manage,action='status');self.assertEqual(status['revision'],0)
            p=await invoke(manage,action='inspect',catalog_path=str(self.catalog));self.assertTrue(p['ok'])
            refused=await invoke(manage,action='init',catalog_path=str(self.catalog),confirmed=False);self.error(refused,'confirmation_required')
            saved=await invoke(manage,action='init',catalog_path=str(self.catalog),confirmed=True,expected_revision=0,expected_preview_sha256=p['preview_sha256']);self.assertTrue(saved['ok'])
            r=await invoke(report,reference_date='2026-10-31',horizon_months=1);self.assertEqual(r['document_count'],6)
            c=self.root/'家庭台账-确认替换.json';p2=await invoke(manage,action='inspect',catalog_path=str(c))
            saved2=await invoke(manage,action='update',catalog_path=str(c),confirmed=True,expected_revision=1,expected_preview_sha256=p2['preview_sha256']);self.assertEqual(saved2['revision'],2)
            stale=await invoke(manage,action='update',catalog_path=str(c),confirmed=True,expected_revision=1,expected_preview_sha256=p2['preview_sha256']);self.error(stale,'revision_conflict')
            plan=await invoke(pack,plan_path=str(self.plan),output_dir=str(self.output));self.assertTrue(plan['complete'])
            refused=await invoke(pack,plan_path=str(self.plan),output_dir=str(self.output),mode='build',confirmed=False);self.error(refused,'confirmation_required')
            result=await invoke(pack,plan_path=str(self.plan),output_dir=str(self.output),mode='build',confirmed=True,expected_revision=2,expected_preview_sha256=plan['preview_sha256']);self.assertTrue(result['ok'])
            repeated=await invoke(pack,plan_path=str(self.plan),output_dir=str(self.output),mode='build',confirmed=True,expected_revision=2,expected_preview_sha256=plan['preview_sha256']);self.error(repeated,'output_exists')
            uncertain=await invoke(pack,plan_path=str(self.root/'材料计划-待确认.json'),output_dir=str(self.root/'待确认副本'));self.assertFalse(uncertain['complete'])
            invalid=await invoke(manage,action='inspect',catalog_path=str(self.root/'重复键.json'));self.error(invalid,'duplicate_json_key')
            stream=[x async for x in report.stream({'workspace':str(self.root),'reference_date':'2026-10-31','horizon_months':1})]
            actual.append({'class':report.__class__.__name__,'stream':True,'result':stream})
            self.assertEqual(stream,[await invoke(report,reference_date='2026-10-31',horizon_months=1)])
        asyncio.run(exercise())
        if os.environ.get('FAMILY_SDK_RESULT'):
            Path(os.environ['FAMILY_SDK_RESULT']).write_text(json.dumps({'version':'1.0.0','payload':str(PAYLOAD),
                'actual_tool_calls':len(actual),'passed':True,'results':actual},ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
