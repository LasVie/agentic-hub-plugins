"""Functional tests: ledger atomicity, policy concurrency, corruption and Chinese flows."""
from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
PAYLOAD=Path(os.environ.get("MESSAGE_QUOTA_TEST_PAYLOAD",REPO/"plugins/message-quota-audit/message-quota-audit"))
spec=importlib.util.spec_from_file_location("quota_test_core",PAYLOAD/"runtime/quota.py")
q=importlib.util.module_from_spec(spec)
# Test imports must not mutate the source payload inspected by check-repo.
_previous_bytecode=sys.dont_write_bytecode
try:
    sys.dont_write_bytecode=True
    spec.loader.exec_module(q)
finally:
    sys.dont_write_bytecode=_previous_bytecode
NOW=int(datetime(2026,10,23,8,tzinfo=timezone.utc).timestamp()*1000)


def message(number=1,**overrides):
    return {"id":f"msg_{number}","as":"sender_demo","targets":["reader_a"],"type":"direct","mode":"online","body":"这是需要认真讨论的中文进度。","hop":0,**overrides}


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="message-quota-tests-")
        self.w=str(Path(self.temp.name).resolve())
        self.assertTrue(self.call("policy",action="init")["ok"])
    def tearDown(self):self.temp.cleanup()
    def call(self,op,now=NOW,**kw):return q.dispatch(op,{"workspace":self.w,**kw},now_ms=now)
    def check(self,m=None,**kw):return self.call("check",message_json=q.packed(m or message()),**kw)
    def record(self,m=None,**kw):return self.call("record",message_json=q.packed(m or message()),confirmed=True,**kw)
    def configure(self,**kw):
        status=self.call("policy",action="status");p=copy.deepcopy(status["policy"]);p.update(kw)
        return self.call("policy",action="configure",expected_revision=status["revision"],policy_json=q.packed(p))
    def code(self,r,expected):self.assertFalse(r["ok"],r);self.assertEqual(r["error"]["code"],expected)
    def test_read_only_preview_and_no_body_persistence(self):
        db=Path(self.w)/q.STATE/"ledger.sqlite3";before=db.read_bytes()
        r=self.check();self.assertEqual(r["verdict"],"allowed");self.assertFalse(r["recorded"])
        self.call("report");self.call("policy",action="status");self.assertEqual(before,db.read_bytes())
        self.record();self.assertNotIn(message()["body"].encode(),db.read_bytes());self.assertNotIn(message()["body"],q.packed(r))
    def test_exact_limit_and_next_reject(self):
        self.configure(buckets={"direct":{"limit":2,"per_send":False}},pair_max=20)
        self.assertTrue(self.record(message(1))["recorded"]);self.assertTrue(self.record(message(2))["recorded"])
        r=self.record(message(3));self.assertEqual(r["reason_code"],"quota_exceeded");self.assertFalse(r["recorded"])
        self.assertEqual(self.call("report")["event_count"],2)
    def test_preview_not_reservation(self):
        self.configure(buckets={"direct":{"limit":1,"per_send":False}})
        self.assertEqual(self.check(message(1))["verdict"],"allowed");self.assertEqual(self.check(message(2))["verdict"],"allowed")
        self.record(message(2));self.assertEqual(self.record(message(1))["reason_code"],"quota_exceeded")
    def test_recipient_and_offline_units(self):
        self.assertEqual(self.record(message(targets=["a","b"]))["units"],2)
        self.assertEqual(self.record(message(2,targets=["a","b"],mode="offline",body="收到",hop=100))["units"],1)
        self.assertEqual(self.call("report")["event_count"],2)
    def test_per_send_bucket_and_separate_sender(self):
        self.configure(buckets={"direct":{"limit":1,"per_send":True}},pair_max=20)
        self.assertEqual(self.record(message(targets=["a","b"]))["units"],1)
        self.assertTrue(self.record(message(2,**{"as":"another"}))["recorded"])
    def test_unknown_bucket_and_zero_limit(self):
        self.code(self.check(message(type="missing")),"unknown_bucket")
        self.configure(buckets={"direct":{"limit":0,"per_send":False}})
        self.assertEqual(self.check()["reason_code"],"quota_exceeded")
    def test_ack_chinese_english_and_hop(self):
        for text in ["收到，谢谢！","got it — thanks"]:self.assertEqual(self.check(message(body=text))["reason_code"],"ack_only")
        self.assertEqual(self.check(message(hop=3))["reason_code"],"hop_limit")
        self.configure(ack_max_bytes=0);self.assertEqual(self.check(message(body="收到"))["verdict"],"allowed")
    def test_pair_window_across_day_and_bucket(self):
        self.configure(pair_max=1,buckets={"direct":{"limit":99,"per_send":False},"second":{"limit":99,"per_send":False}})
        self.record(now=NOW)
        self.assertEqual(self.check(message(2,type="second"),now=NOW+1199999)["reason_code"],"pair_limit")
        self.assertEqual(self.check(message(2),now=NOW+1200000)["verdict"],"allowed")
    def test_duplicate_record_and_conflict(self):
        self.record();r=self.record();self.assertTrue(r["duplicate"]);self.assertEqual(r["verdict"],"already_recorded")
        self.code(self.record(message(body="内容已改变。")),"event_conflict")
        self.assertEqual(self.call("report")["event_count"],1)
    def test_canonical_recipient_order(self):
        self.record(message(targets=["b","a"]));self.assertTrue(self.record(message(targets=["a","b"]))["duplicate"])
    def test_explicit_confirm(self):
        self.code(self.call("record",message_json=q.packed(message()),confirmed=False),"confirmation_required")
        self.assertEqual(self.call("report")["event_count"],0)
    def test_revision_conflict_and_init_preserves(self):
        self.record();self.configure(pair_max=4)
        self.code(self.call("policy",action="configure",expected_revision=0,policy_json=q.packed(q.DEFAULT)),"revision_conflict")
        r=self.call("policy",action="init");self.assertEqual((r["revision"],r["event_count"]),(1,1))
        self.assertEqual(self.configure()["revision"],1)
    def test_locked_timezone_and_day_boundary(self):
        self.record();self.code(self.configure(timezone="UTC"),"time_policy_locked");self.code(self.configure(day_boundary_hour=9),"time_policy_locked")
    def test_day_rollover_named_zone(self):
        self.configure(timezone="Asia/Shanghai",day_boundary_hour=9,pair_max=100,buckets={"direct":{"limit":1,"per_send":False}})
        early=int(datetime(2026,10,23,0,59,59,tzinfo=timezone.utc).timestamp()*1000)
        r=self.record(now=early);self.assertEqual(r["day"],"2026-10-22")
        r=self.record(message(2),now=early+1000);self.assertEqual(r["day"],"2026-10-23");self.assertTrue(r["recorded"])
    def test_dst_wall_clock_boundary(self):
        p={**q.DEFAULT,"timezone":"America/New_York","day_boundary_hour":2}
        # Spring-forward wall clock jumps from 01:59 to03:00, past the declared boundary.
        a=int(datetime(2026,3,8,6,59,tzinfo=timezone.utc).timestamp()*1000)
        self.assertEqual(q.day_of(a,p),"2026-03-07");self.assertEqual(q.day_of(a+60000,p),"2026-03-08")
    def test_event_time_and_clock_rollback(self):
        self.code(self.check(message(sentAtMs=NOW+1)),"invalid_event_time")
        self.code(self.check(message(sentAtMs=NOW-300001)),"invalid_event_time")
        self.assertTrue(self.record(message(sentAtMs=NOW-1000))["recorded"])
        self.code(self.check(message(2),now=NOW-1),"clock_rollback")
        self.code(self.call("report",now=NOW-1),"clock_rollback")
    def test_reconcile_match_missing_changed_substitution(self):
        self.record();self.record(message(2,mode="offline"));report=self.call("report")
        for entries,match in [(report["entries"],True),(report["entries"][:1],False),([{**report["entries"][0],"id":"substitute"},report["entries"][1]],False)]:
            r=self.call("report",action="reconcile",entries_json=q.packed(entries));self.assertEqual(r["matched"],match)
        self.code(self.call("report",action="reconcile",entries_json=q.packed(report["entries"]*2)),"duplicate_entry")
        self.assertEqual(self.call("report")["event_count"],2)
    def test_report_range_not_all_stored_days(self):
        self.record();self.record(message(2),now=NOW+86400000)
        r=self.call("report",days=1,now=NOW+86400000);self.assertEqual(r["event_count"],1);self.assertEqual(r["entries"][0]["id"],"msg_2")
    def test_concurrent_admission_does_not_exceed_limit(self):
        self.configure(pair_max=100,buckets={"direct":{"limit":7,"per_send":False}})
        with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(lambda n:self.record(message(n)),range(20)))
        self.assertTrue(all(r["ok"] for r in results),results)
        self.assertEqual(sum(r["recorded"] for r in results),7);self.assertEqual(self.call("report")["event_count"],7)
    def test_concurrent_same_id_idempotent(self):
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:self.record(),range(12)))
        self.assertTrue(all(r["recorded"] for r in results));self.assertEqual(sum(not r["duplicate"] for r in results),1)
        self.assertEqual(self.call("report")["event_count"],1)
    def test_corrupt_bytes_and_empty_not_reset(self):
        db=Path(self.w)/q.STATE/"ledger.sqlite3"
        for content in (b"not a database",b""):
            db.write_bytes(content)
            self.code(self.call("policy",action="init"),"corrupt_state");self.assertEqual(db.read_bytes(),content)
    def test_missing_schema_not_reset(self):
        db=Path(self.w)/q.STATE/"ledger.sqlite3"
        with sqlite3.connect(db) as con:con.execute("DROP TABLE events")
        self.code(self.call("policy",action="init"),"corrupt_state")
    def test_replaced_schema_fails_as_structured_error(self):
        db=Path(self.w)/q.STATE/"ledger.sqlite3"
        with sqlite3.connect(db) as con:
            con.execute("DROP TABLE events");con.execute("CREATE TABLE events(wrong TEXT)");con.execute("INSERT INTO events VALUES('damaged')")
        self.code(self.check(),"corrupt_state");self.code(self.record(),"corrupt_state");self.code(self.call("policy",action="init"),"corrupt_state")
    def test_damaged_record_not_silently_skipped(self):
        self.record();db=Path(self.w)/q.STATE/"ledger.sqlite3"
        with sqlite3.connect(db) as con:con.execute("UPDATE events SET targets='not json'")
        self.code(self.check(message(2)),"corrupt_state");self.code(self.call("report"),"corrupt_state")
    def test_separate_processes_share_atomic_limit(self):
        self.configure(pair_max=100,buckets={"direct":{"limit":3,"per_send":False}})
        cli=PAYLOAD/"scripts/quota_cli.py"
        procs=[subprocess.Popen([sys.executable,"-B",str(cli),"record"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(8)]
        for n,p in enumerate(procs):
            p.stdin.write(q.packed({"workspace":self.w,"message_json":q.packed(message(n)),"confirmed":True}));p.stdin.close();p.stdin=None
        results=[]
        for p in procs:
            out,err=p.communicate(timeout=15);self.assertEqual(p.returncode,0,err);results.append(json.loads(out))
        self.assertEqual(sum(r["recorded"] for r in results),3)
    def test_sqlite_writer_lock_fails_without_false_success(self):
        db=Path(self.w)/q.STATE/"ledger.sqlite3"
        with sqlite3.connect(db) as con:
            con.execute("BEGIN IMMEDIATE")
            self.code(self.record(),"state_busy")
        self.assertEqual(self.call("report")["event_count"],0)
    def test_bad_permissions_and_symlink(self):
        directory=Path(self.w)/q.STATE;directory.chmod(0o755);self.code(self.check(),"unsafe_state");directory.chmod(0o700)
        db=directory/"ledger.sqlite3";saved=db.read_bytes();db.unlink();target=Path(self.w)/"outside.db";target.write_bytes(saved);db.symlink_to(target)
        self.code(self.check(),"unsafe_state");self.assertEqual(target.read_bytes(),saved)
    def test_no_path_from_sender_and_invalid_requests(self):
        for edits in [{"as":"../escape"},{"targets":["a","a"]},{"hop":True},{"force":True},{"body":"\ud800"}]:
            try:r=self.check(message(**edits))
            except UnicodeError:r=q.dispatch("check",{"workspace":self.w,"message_json":json.dumps(message(**edits))},now_ms=NOW)
            self.assertFalse(r["ok"],r)
        self.assertFalse((Path(self.w).parent/"escape").exists())
    def test_duplicate_json_and_nonfinite(self):
        for text in ['{"id":1,"id":2}','{"x":NaN}']:
            r=self.call("check",message_json=text);self.assertFalse(r["ok"]);self.assertTrue(any('\u4e00'<=c<='\u9fff' for c in r["error"]["message"]))
    def test_invalid_policy_types_and_unknown_zone(self):
        self.code(self.configure(pair_max=True),"invalid_policy");self.code(self.configure(timezone="No/Such_Zone"),"timezone_unavailable")
        self.code(self.configure(buckets={"direct":{"limit":-1,"per_send":False}}),"invalid_policy")
    def test_cli_real_json_and_chinese_help(self):
        cli=PAYLOAD/"scripts/quota_cli.py"
        p=subprocess.run([sys.executable,"-B",str(cli),"check"],input=q.packed({"workspace":self.w,"message_json":q.packed(message())}),text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)["verdict"],"allowed")
        p=subprocess.run([sys.executable,"-B",str(cli),"--help"],text=True,capture_output=True);self.assertEqual(p.returncode,0);self.assertIn("用法",p.stdout)


if __name__=="__main__":unittest.main()
