"""Check the command line, serialized handoffs and actual HTML output."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TEAM = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get("LISTING_TEST_PAYLOAD", TEAM / TEAM.name))
CLI = PAYLOAD / "skills/listing-photo-review/scripts/review.py"
FIXTURES = TEAM / "tests/fixtures"


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class ListingReviewTest(unittest.TestCase):
    def setUp(self):
        scratch_root = TEAM / ".local"
        scratch_root.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix="test-", dir=scratch_root)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(FIXTURES, self.root, dirs_exist_ok=True)
        self.source = self.root / "products.json"
        self.photos = self.root / "photos"
        self.batch = self.root / "batch/batch.json"
        self.first = self.root / "evidence-answer.json"
        self.second = self.root / "verify-answer.json"

    def cli(self, stage, out, *args, error=None):
        dest = self.root / out
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), stage, "--source", str(self.source),
             "--photos", str(self.photos), "--out", str(dest), *map(str, args)],
            capture_output=True, text=True, check=False,
        )
        if error:
            self.assertEqual(result.returncode, 2, result)
            self.assertIn("无法完成照片复核阶段", result.stderr)
            self.assertIn(error, result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("已保存", result.stdout)
        return dest

    def prepare(self):
        self.cli("prepare", "batch")
        return load(self.batch)

    def seal(self, role, answer, *, error=None):
        return self.cli("seal", role, "--batch", self.batch, "--role", role,
                        "--answer", answer, error=error) / "review.json"

    def deliver(self, first, second, *, error=None):
        return self.cli("deliver", "delivery", "--batch", self.batch,
                        "--evidence", first, "--verify", second, error=error)

    def round(self):
        self.prepare()
        return self.seal("evidence", self.first), self.seal("verifier", self.second)

    def test_ready_order_and_held_item_with_read_only_sources(self):
        original = {p: p.read_bytes() for p in [self.source, *self.photos.rglob("*")] if p.is_file()}
        first, second = self.round()
        out = self.deliver(first, second)
        data = load(out / "report.json")
        self.assertEqual(data["evidence_sha256"], sha256(first.read_bytes()).hexdigest())
        self.assertEqual(data["verification_sha256"], sha256(second.read_bytes()).hexdigest())
        self.assertEqual(data["items"][0]["cover"], "camera/front.jpg")
        self.assertEqual(data["items"][0]["order"],
                         ["camera/front.jpg", "camera/right-scratch.png", "camera/charger.png"])
        hold = data["items"][1]
        self.assertEqual((hold["status"], hold["cover"], hold["order"]), ("hold", None, []))
        self.assertEqual(hold["issues"][0]["status"], "retake")
        html = (out / "checklist.html").read_text()
        self.assertIn('lang="zh-CN"', html)
        self.assertIn("照片复核通过", html)
        self.assertIn("暂缓", html)
        self.assertIn("打开的钻头盒", html)
        self.assertEqual(original, {p: p.read_bytes() for p in original})

    def test_disjoint_cover_and_evidence_remain_held(self):
        other = load(self.second)
        other["items"]["C01"]["covers"] = ["p02"]
        other["items"]["C01"]["checks"]["c02"]["photos"] = ["p03"]
        save(self.second, other)
        out = self.deliver(*self.round())
        item = load(out / "report.json")["items"][0]
        self.assertEqual(item["order"], [])
        self.assertEqual([p["status"] for p in item["issues"]], ["confirm", "confirm"])

    def test_unreadable_photo_never_satisfies_check(self):
        other = load(self.second)
        other["items"]["C01"]["photos"]["p02"] = "confirm"
        save(self.second, other)
        self.prepare()
        self.assertFalse(self.seal("verifier", self.second, error="批次外的照片编号").exists())

    def test_missing_photo_observation_or_unknown_item_rejected(self):
        self.prepare()
        bad = load(self.first)
        del bad["items"]["C01"]["photos"]["p02"]
        save(self.first, bad)
        self.seal("evidence", self.first, error="记录字段")
        bad = load(FIXTURES / self.first.name)
        bad["items"]["fake"] = bad["items"]["C01"]
        save(self.first, bad)
        self.seal("evidence", self.first, error="记录字段")

    def test_changed_source_refuses_seal(self):
        self.prepare()
        source = load(self.source)
        source["items"][0]["checks"][1] = "左侧划痕"
        save(self.source, source)
        self.seal("evidence", self.first, error="已变化")

    def test_changed_photo_refuses_delivery(self):
        first, second = self.round()
        p = self.photos / "camera/front.jpg"
        p.write_bytes(p.read_bytes() + b"changed")
        self.assertFalse(self.deliver(first, second, error="已变化").exists())

    def test_wrong_role_and_missing_receipt_do_not_deliver(self):
        first, second = self.round()
        self.deliver(first, first, error="指定角色不符")
        self.deliver(first, second.with_name("missing.json"), error="普通 JSON 文件")

    def test_other_batch_hash_cannot_deliver(self):
        first, second = self.round()
        other = load(second)
        other["batch_sha256"] = "0" * 64
        save(second, other)
        self.deliver(first, second, error="当前批次")

    def test_cross_item_duplicate_content_rejected(self):
        shutil.copyfile(self.photos / "camera/right-scratch.png", self.photos / "drill/front.png")
        self.cli("prepare", "batch", error="两个商品引用了相同照片")

    def test_duplicate_within_item_yields_one_file_per_content(self):
        shutil.copyfile(self.photos / "camera/right-scratch.png", self.photos / "camera/charger.png")
        item = load(self.deliver(*self.round()) / "report.json")["items"][0]
        self.assertEqual(item["order"], ["camera/front.jpg", "camera/right-scratch.png"])

    def test_traversal_and_symlink_rejected(self):
        source = load(self.source)
        source["items"][0]["photos"][0] = "../products.json"
        save(self.source, source)
        self.cli("prepare", "batch", error="相对路径")
        source["items"][0]["photos"][0] = "alias.jpg"
        (self.photos / "alias.jpg").symlink_to(self.photos / "camera/front.jpg")
        save(self.source, source)
        self.cli("prepare", "batch", error="符号链接")

    def test_html_escapes_input_and_prevents_overwrite(self):
        source = load(self.source)
        source["items"][0]["title"] = "<script>示例</script>"
        save(self.source, source)
        first, second = self.round()
        out = self.deliver(first, second)
        original = (out / "checklist.html").read_bytes()
        self.assertIn(b"&lt;script&gt;", original)
        self.assertNotIn(b"<script>", original)
        self.deliver(first, second, error="目录已存在")
        self.assertEqual(original, (out / "checklist.html").read_bytes())


if __name__ == "__main__":
    unittest.main()
