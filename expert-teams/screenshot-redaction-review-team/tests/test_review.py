"""Check the native CLI from source or the exact extracted package."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from zlib import crc32


TEAM = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("REDACTION_TEST_PAYLOAD", TEAM / TEAM.name))
FIXTURE = TEAM / "tests/fixtures/screenshots"
MASK = {"x": 45, "y": 151, "w": 670, "h": 72}
KEEP = {"x": 56, "y": 250, "w": 700, "h": 66}
MARKERS = ("sandbox-only@example.test", "practice-account@example.test", "SYNTHETIC_META_SENTINEL")


def checksum(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def png_chunks(path):
    data = path.read_bytes()[8:]
    while data:
        n, name = struct.unpack(">I4s", data[:8])
        yield name, data[8:8+n]
        data = data[n+12:]


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = TEAM / ".local"
        scratch.mkdir(exist_ok=True)
        cls.build = tempfile.TemporaryDirectory(prefix="tests-", dir=scratch)
        cls.addClassCleanup(cls.build.cleanup)
        cls.tool = Path(cls.build.name) / "review"
        subprocess.run(["/usr/bin/swiftc","-O","-module-cache-path",str(scratch/"swift-modules"),
                        str(PAYLOAD/"skills/screenshot-review/scripts/review.swift"),"-o",str(cls.tool)], check=True)

    def setUp(self):
        scratch = tempfile.TemporaryDirectory(dir=self.build.name)
        self.addCleanup(scratch.cleanup)
        self.dir = Path(scratch.name)
        self.src = self.dir/"source"
        shutil.copytree(FIXTURE, self.src)
        self.scanpath = self.dir/"scan.json"
        self.planpath = self.dir/"approval.json"
        self.candidate = self.dir/"candidate"
        self.audit = self.dir/"audit.json"
        self.delivery = self.dir/"delivery"

    def command(self, *args, ok=True):
        result = subprocess.run([str(self.tool), *map(str,args)], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        for marker in MARKERS:
            self.assertNotIn(marker, result.stdout + result.stderr)
        return result

    def prepare(self, categories="manual"):
        self.command("scan", self.src, self.scanpath, categories)
        for marker in MARKERS:
            self.assertNotIn(marker, self.scanpath.read_text())
        plan = {"version":"1.0.0","scanSHA256":checksum(self.scanpath),"images":[
            {"id":"image-01","disposition":"held","masks":[],"keep":[],"dismissed":[]},
            {"id":"image-02","disposition":"approved","masks":[MASK],"keep":[KEEP],"dismissed":[]},
        ]}
        write_json(self.planpath, plan)
        return plan

    def inputs(self):
        return self.src,self.scanpath,self.planpath,self.candidate

    def render(self):
        self.command("render", *self.inputs())

    def verify(self, ok=True):
        return self.command("verify", *self.inputs(), self.audit, ok=ok)

    def deliver(self, ok=True):
        return self.command("deliver", *self.inputs(), self.audit, self.delivery, ok=ok)

    def test_complete_bundle_and_package_free_of_source_metadata(self):
        self.prepare()
        self.render()
        self.verify()
        self.deliver()
        assert_image = self.delivery/"share/image-02.png"
        kinds = {k for k,_ in png_chunks(assert_image)}
        self.assertEqual(kinds, {b"IHDR",b"IDAT",b"IEND"})
        self.assertEqual(list((self.delivery/"share").iterdir()), [assert_image])
        self.assertEqual(json.loads(self.audit.read_bytes())["filesSHA256"], {"image-02.png":checksum(assert_image)})
        self.assertEqual(json.loads(self.audit.read_bytes())["held"], ["image-01"])
        self.assertIn("1 张通过", (self.delivery/"checklist.html").read_text())
        self.assertNotIn(b"SYNTHETIC_META_SENTINEL", assert_image.read_bytes())
        self.assertIn(b"SYNTHETIC_META_SENTINEL", (self.src/"support-2.png").read_bytes())
        self.deliver(ok=False)

    def test_kept_area_overlap_blocks_candidate(self):
        plan = self.prepare()
        plan["images"][1]["keep"] = [MASK]
        write_json(self.planpath, plan)
        result = self.command("render", *self.inputs(), ok=False)
        self.assertIn("必须保留的区域", result.stderr)
        self.assertFalse(self.candidate.exists())

    def test_out_of_bounds_rejected(self):
        plan = self.prepare()
        plan["images"][1]["masks"][0] = {"x":500,"y":0,"w":500,"h":5}
        write_json(self.planpath, plan)
        self.command("render", *self.inputs(), ok=False)

    def test_png_ancillary_chunk_is_rejected(self):
        self.prepare()
        self.render()
        p = self.candidate/"image-02.png"
        png = p.read_bytes()
        payload = b"tEXtComment\0SYNTHETIC_META_SENTINEL"
        chunk = struct.pack(">I",len(payload)-4) + payload + struct.pack(">I",crc32(payload))
        p.write_bytes(png[:-12]+chunk+png[-12:])
        self.assertIn("额外数据块", self.verify(ok=False).stderr)
        self.assertFalse(self.audit.exists())

    def test_decoded_pixel_check_catches_a_smaller_mask(self):
        plan = self.prepare()
        small = self.dir/"small.json"
        altered = dict(plan["images"][1], masks=[dict(MASK,w=130)])
        write_json(small, dict(plan, images=[plan["images"][0],altered]))
        self.command("render", self.src,self.scanpath,small,self.candidate)
        self.assertIn("未完整覆盖", self.verify(ok=False).stderr)

    def test_decoded_pixel_check_catches_changed_unmasked_region(self):
        plan = self.prepare()
        changed = self.dir/"large.json"
        altered = dict(plan["images"][1], masks=[dict(MASK,w=755)])
        write_json(changed, dict(plan, images=[plan["images"][0],altered]))
        self.command("render", self.src,self.scanpath,changed,self.candidate)
        self.assertIn("框之外", self.verify(ok=False).stderr)

    def test_after_review_modified_package_or_receipt_is_rejected(self):
        self.prepare()
        self.render()
        self.verify()
        self.audit.write_bytes(self.audit.read_bytes()+b" ")
        self.assertIn("正式复核记录", self.deliver(ok=False).stderr)
        self.assertFalse(self.delivery.exists())

    def test_source_swap_rejected(self):
        self.prepare()
        self.render()
        first, second = [self.src/f"support-{i}.png" for i in (1,2)]
        first.write_bytes(second.read_bytes())
        self.assertIn("原图已更换", self.verify(ok=False).stderr)

    def test_uncovered_suggestion_cannot_pass(self):
        plan = self.prepare()
        value = json.loads(self.scanpath.read_bytes())
        value["images"][1]["suggestions"] = [{"kind":"email","box":KEEP}]
        write_json(self.scanpath, value)
        plan["scanSHA256"] = checksum(self.scanpath)
        write_json(self.planpath,plan)
        self.assertIn("未覆盖", self.command("render",*self.inputs(),ok=False).stderr)

    def test_extra_candidate_file_rejected(self):
        self.prepare()
        self.render()
        (self.candidate/"extra.txt").write_text("test")
        self.assertIn("多余或缺失", self.verify(ok=False).stderr)

    def test_all_held_yields_no_shareable_files(self):
        plan=self.prepare()
        plan["images"][1]["disposition"]="held"
        write_json(self.planpath,plan)
        self.render()
        self.verify()
        self.deliver()
        self.assertEqual(list((self.delivery/"share").iterdir()),[])
        self.assertIn("2 张暂缓",(self.delivery/"checklist.html").read_text())

    def test_vision_recognizes_synthetic_email(self):
        if not os.environ.get("REDACTION_TEST_VISION"):
            self.skipTest("Vision needs local macOS framework access")
        self.prepare("email")
        scan = json.loads(self.scanpath.read_bytes())
        self.assertTrue(any(r["kind"]=="email" for r in scan["images"][1]["suggestions"]))
        self.render()
        self.verify()


if __name__ == "__main__":
    unittest.main()
