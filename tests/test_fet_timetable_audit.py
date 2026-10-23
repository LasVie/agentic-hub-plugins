"""Functional tests for the actual offline FET audit library and host tools.

Run ``python -m unittest discover -s tests -p test_fet_timetable_audit.py -v``.
Set FET_AUDIT_PAYLOAD to an extracted inner plugin directory to test release
bytes. Host tests require the real openJiuwen SDK; they invoke tools directly
without any model/network call. No replacement SDK or fake tool is used.
``python tests/test_fet_timetable_audit.py --write-demo-dir /absolute/path``
copies independently authored, fictional Chinese inputs for manual testing.
"""
from __future__ import annotations

import asyncio
import copy
from contextlib import contextmanager
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get(
    "FET_AUDIT_PAYLOAD", ROOT / "plugins/fet-timetable-audit/fet-timetable-audit"
)).resolve()
FIXTURES = ROOT / "tests/fixtures/fet-timetable-audit"
VERSION = "1.0.0"


@contextmanager
def immutable_payload_import():
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        yield
    finally:
        sys.dont_write_bytecode = previous


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Functional tests must leave the release payload clean for check-repo.
    with immutable_payload_import():
        spec.loader.exec_module(module)
    return module


def make_demo_fixtures(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for source in sorted(FIXTURES.iterdir()):
        if source.suffix not in {".fet", ".xml"}:
            continue
        target = destination / source.name
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise FileExistsError(f"拒绝覆盖内容不同的文件：{target}")
        if not target.exists():
            shutil.copyfile(source, target)
        files[source.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    return {
        "directory": str(destination), "files": files,
        "说明": "所有学校、教师和班级均为虚构，仅用于离线功能测试。",
        "示例学校.fet": "3项活动、共4节；张老师3节，李老师1节。",
        "无冲突课表.xml": "已支持的审查项目应通过；不等于验证FET的全部约束。",
        "冲突课表.xml": "应报告教师重叠、学生重叠和教师不可用时段。",
    }


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fet-audit-functional-")
        self.directory = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        make_demo_fixtures(self.directory)
        self.fet = self.directory / "示例学校.fet"
        self.solution = self.directory / "无冲突课表.xml"

    def write(self, name, data):
        target = self.directory / name
        target.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return target

    def mutate(self, source, action, name="变体.xml"):
        root = ET.parse(source).getroot()
        action(root)
        return self.write(name, ET.tostring(root, encoding="utf-8", xml_declaration=True))

    def move(self, identifier, day, hour, name="移动课表.xml"):
        def action(root):
            node = next(a for a in root.findall("Activity") if a.findtext("Id") == identifier)
            node.find("Day").text = day
            node.find("Hour").text = hour
        return self.mutate(self.solution, action, name)

    def assert_chinese(self, text):
        self.assertIsInstance(text, str)
        self.assertRegex(text, r"[\u4e00-\u9fff]", text)
        self.assertNotIn("\ufffd", text)

    def success(self, result):
        self.assertIs(result.get("ok"), True, result)
        self.assertEqual(result.get("version"), VERSION, result)
        return result

    def rejected(self, result, code=None):
        self.assertIs(result.get("ok"), False, result)
        self.assertEqual(result.get("version"), VERSION, result)
        self.assert_chinese(result["error"]["message"])
        if code:
            self.assertEqual(result["error"]["code"], code, result)
        return result

    def issue(self, result, code):
        self.success(result)
        self.assertIs(result["passed"], False, result)
        issues = [i for i in result["issues"] if i["code"] == code]
        self.assertTrue(issues, (code, result))
        for item in issues:
            self.assert_chinese(item["message"])
        return issues


class FetAuditCoreTests(FixtureCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_module("fet_audit_functional", PAYLOAD / "lib/fet_audit.py")

    def inspect(self, path=None):
        return self.core.inspect_fet(str(path or self.fet))

    def verify(self, solution=None, fet=None):
        return self.core.verify_timetable(str(fet or self.fet), str(solution or self.solution))

    def test_valid_chinese_school_references_and_workloads(self):
        result = self.success(self.inspect())
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["issues_found"], 0, result)
        self.assertEqual(result["issues"], [], result)
        self.assertEqual(result["summary"]["active_activities"], 3)
        self.assertEqual(result["summary"]["total_duration"], 4)
        teachers = {row["name"]: row for row in result["workload"]["teachers"]}
        self.assertEqual(teachers["张老师"]["duration"], 3)
        self.assertEqual(teachers["张老师"]["available_slots"], 7)
        self.assertEqual(teachers["李老师"]["duration"], 1)
        self.assertEqual(teachers["李老师"]["available_slots"], 8)
        students = {row["name"]: row for row in result["workload"]["students"]}
        self.assertEqual(set(students), {"一班甲组", "一班乙组", "二班甲组"})
        self.assertTrue(all(row["duration"] == 2 and row["available_slots"] == 7 for row in students.values()))
        self.assertIs(result["bounded_coverage"]["full_feasibility_checked"], False)
        self.assert_chinese(result["bounded_coverage"]["limitation"])

    def test_valid_timetable_three_activities_four_periods(self):
        result = self.success(self.verify())
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["issues_found"], 0)
        self.assertEqual(result["unplaced"], [])
        self.assertEqual(len(result["rows"]), 3)
        self.assertEqual(sum(row["duration"] for row in result["rows"]), 4)
        self.assertTrue(result["bounded_coverage"])

    def test_conflicting_demo_detects_teacher_students_and_availability(self):
        result = self.verify(self.directory / "冲突课表.xml")
        for code in ("teacher_overlap", "students_overlap", "teacher_unavailable"):
            self.issue(result, code)

    def test_missing_declared_references_are_findings(self):
        for tag, replacement, code in (
            ("Teacher", "未登记教师", "unknown_teacher"),
            ("Subject", "未登记科目", "unknown_subject"),
            ("Students", "未登记班级", "unknown_students"),
        ):
            with self.subTest(reference=tag):
                path = self.mutate(self.fet, lambda root: setattr(
                    root.find(f"Activities_List/Activity/{tag}"), "text", replacement))
                self.issue(self.inspect(path), code)

    def test_duplicate_activity_ids_cannot_silently_overwrite(self):
        def duplicate(root):
            activities = root.find("Activities_List")
            activities.append(copy.deepcopy(activities.find("Activity")))
        self.rejected(self.inspect(self.mutate(self.fet, duplicate)), "duplicate_activity_id")

    def test_duplicate_solution_ids_cannot_silently_overwrite(self):
        path = self.mutate(self.solution, lambda root: root.append(copy.deepcopy(root.find("Activity"))))
        self.rejected(self.verify(path), "duplicate_solution_id")

    def test_numerically_equivalent_activity_ids_are_duplicates(self):
        def duplicate(root):
            activities = root.find("Activities_List")
            node = copy.deepcopy(activities.find("Activity"))
            node.find("Id").text = "00101"
            activities.append(node)
        self.rejected(self.inspect(self.mutate(self.fet, duplicate)), "duplicate_activity_id")

    def test_unknown_solution_id_is_reported(self):
        path = self.mutate(self.solution, lambda root: setattr(root.find("Activity/Id"), "text", "999"))
        result = self.verify(path)
        self.issue(result, "unknown_solution_activity")
        self.issue(result, "unplaced_activity")

    def test_missing_assignment_is_reported(self):
        path = self.mutate(self.solution, lambda root: root.remove(root.find("Activity")))
        result = self.verify(path)
        self.issue(result, "unplaced_activity")
        self.assertIn("101", json.dumps(result["unplaced"]))

    def test_explicit_empty_assignment_is_unplaced(self):
        path = self.move("103", "", "")
        self.issue(self.verify(path), "unplaced_activity")

    def test_invalid_schedule_day_or_hour_is_reported(self):
        for day, hour, code in (("星期八", "第1节", "unknown_day"),
                                ("星期一", "第99节", "unknown_hour")):
            with self.subTest(day=day, hour=hour):
                self.issue(self.verify(self.move("103", day, hour)), code)

    def test_duration_overflow_is_reported(self):
        self.issue(self.verify(self.move("101", "星期一", "第4节")), "duration_overflow")

    def test_duration_must_be_positive_integer(self):
        for duration in ("0", "-1", "1.5", "不是整数", ""):
            with self.subTest(duration=duration):
                path = self.mutate(self.fet, lambda root: setattr(
                    root.find("Activities_List/Activity/Duration"), "text", duration))
                self.rejected(self.inspect(path))

    def test_parent_availability_applies_to_descendant_students(self):
        self.issue(self.verify(self.move("103", "星期二", "第4节")), "students_unavailable")

    def test_parent_group_and_subgroup_overlap(self):
        path = self.mutate(self.fet, lambda root: setattr(
            root.findall("Activities_List/Activity")[1].find("Students"), "text", "一班甲组"))
        self.issue(self.verify(fet=path), "students_overlap")

    def test_disjoint_subgroups_do_not_conflict(self):
        def split(root):
            activities = root.findall("Activities_List/Activity")
            activities[0].find("Students").text = "一班甲组"
            activities[1].find("Students").text = "一班乙组"
        result = self.success(self.verify(fet=self.mutate(self.fet, split)))
        self.assertNotIn("students_overlap", [i["code"] for i in result["issues"]])
        self.assertTrue(result["passed"], result)

    def test_shared_subgroup_across_groups_makes_them_overlap(self):
        def share(root):
            first, second = root.findall("Students_List/Year/Group")
            second.append(copy.deepcopy(first.find("Subgroup")))
        self.issue(self.verify(fet=self.mutate(self.fet, share)), "students_overlap")

    def test_conflicting_repeated_student_hierarchy_is_rejected(self):
        def inconsistent(root):
            year = root.find("Students_List/Year")
            copied = copy.deepcopy(year.find("Group"))
            copied.remove(copied.find("Subgroup"))
            year.append(copied)
        self.rejected(self.inspect(self.mutate(self.fet, inconsistent)), "inconsistent_students")

    def test_workload_above_available_capacity_is_a_finding(self):
        def excessive(root):
            activities = root.find("Activities_List")
            for identifier in (104, 105, 106):
                activity = copy.deepcopy(activities.find("Activity"))
                activity.find("Id").text = str(identifier)
                activities.append(activity)
        result = self.inspect(self.mutate(self.fet, excessive))
        self.issue(result, "workload_exceeds_availability")
        teacher = next(row for row in result["workload"]["teachers"] if row["name"] == "张老师")
        self.assertEqual(teacher["duration"], 9)
        self.assertTrue(teacher["exceeds_available"])

    def test_inactive_activity_not_counted_or_required_in_schedule(self):
        model = self.mutate(self.fet, lambda root: setattr(
            root.findall("Activities_List/Activity")[2].find("Active"), "text", "false"))
        solution = self.mutate(self.solution, lambda root: root.remove(root.findall("Activity")[2]), "仅活动课表.xml")
        result = self.success(self.verify(solution, model))
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["summary"]["active_activities"], 2)
        self.assertEqual(result["summary"]["total_duration"], 3)
        self.assertEqual(result["unplaced"], [])

    def test_inactive_constraint_does_not_create_unavailability(self):
        def deactivate(root):
            root.find("Time_Constraints_List/ConstraintTeacherNotAvailableTimes/Active").text = "false"
        model = self.mutate(self.fet, deactivate)
        result = self.success(self.verify(self.move("103", "星期一", "第4节"), model))
        self.assertNotIn("teacher_unavailable", [i["code"] for i in result["issues"]])

    def test_soft_availability_is_not_misrepresented_as_hard_check(self):
        def soften(root):
            root.find("Time_Constraints_List/ConstraintTeacherNotAvailableTimes/Weight_Percentage").text = "50"
        model = self.mutate(self.fet, soften)
        result = self.success(self.verify(self.move("103", "星期一", "第4节"), model))
        self.assertNotIn("teacher_unavailable", [i["code"] for i in result["issues"]])
        self.assertIn("ConstraintTeacherNotAvailableTimes", json.dumps(result["bounded_coverage"]))

    def test_unsupported_constraint_is_explicit_in_coverage(self):
        def add(root):
            node = ET.SubElement(root.find("Time_Constraints_List"), "ConstraintTeacherMaxHoursDaily")
            for key, value in {"Weight_Percentage": "100", "Teacher_Name": "张老师",
                               "Maximum_Hours_Daily": "1", "Active": "true"}.items():
                ET.SubElement(node, key).text = value
        result = self.success(self.verify(fet=self.mutate(self.fet, add)))
        coverage = result["bounded_coverage"]
        self.assertIn("ConstraintTeacherMaxHoursDaily", json.dumps(coverage["unsupported_constraints"]))

    def test_invalid_constraint_day_is_reported(self):
        model = self.mutate(self.fet, lambda root: setattr(root.find(
            "Time_Constraints_List/ConstraintTeacherNotAvailableTimes/Not_Available_Time/Day"), "text", "星期八"))
        self.issue(self.inspect(model), "unknown_day")

    def test_utf8_bom_and_xml_declaration(self):
        path = self.write("带字节顺序标记.fet", b"\xef\xbb\xbf" + self.fet.read_bytes())
        self.assertTrue(self.success(self.inspect(path))["passed"])

    def test_malformed_xml_and_wrong_root_return_chinese_errors(self):
        for data in ("<fet>", "<not_fet />", "无效XML", b"\xff\xfe\x00"):
            with self.subTest(data=data):
                self.rejected(self.inspect(self.write("错误.fet", data)))

    def test_dtd_and_entity_declarations_are_rejected_without_expansion(self):
        for data in (
            '<!DOCTYPE fet [<!ENTITY sample "内容">]><fet>&sample;</fet>',
            '<!DOCTYPE fet SYSTEM "file:///etc/passwd"><fet />',
        ):
            with self.subTest(data=data):
                self.rejected(self.inspect(self.write("实体.fet", data)), "xml_forbidden")

    def test_invalid_path_inputs(self):
        for value in (None, [], {}, 0, True, "", "relative.fet", "https://example.com/test.fet", "/tmp/a\0.fet"):
            with self.subTest(path=value):
                self.rejected(self.core.inspect_fet(value))

    def test_missing_directory_symlink_and_fifo_inputs(self):
        self.rejected(self.inspect(self.directory / "不存在.fet"))
        self.rejected(self.inspect(self.directory))
        link = self.directory / "链接.fet"
        link.symlink_to(self.fet)
        self.rejected(self.inspect(link), "symlink_path")
        parent_link = self.directory / "目录链接"
        parent_link.symlink_to(self.directory, target_is_directory=True)
        self.rejected(self.inspect(parent_link / self.fet.name), "symlink_path")
        if hasattr(os, "mkfifo"):
            fifo = self.directory / "管道.fet"
            os.mkfifo(fifo)
            self.rejected(self.inspect(fifo), "invalid_file")

    def test_oversized_input_is_rejected(self):
        path = self.write("过大.fet", b" " * (8 * 1024 * 1024 + 1))
        self.rejected(self.inspect(path))

    def test_deep_xml_is_rejected(self):
        path = self.write("过深.fet", "<fet>" + "<n>" * 100 + "</n>" * 100 + "</fet>")
        self.rejected(self.inspect(path))

    def test_csv_and_json_export_are_unicode_and_filterable(self):
        result = self.success(self.core.export_timetable(str(self.fet), str(self.solution), "csv"))
        rows = list(csv.reader(io.StringIO(result["content"])))
        self.assertEqual(len(rows), 4)
        self.assertEqual(result["row_count"], 3)
        self.assertIn("数学", result["content"])
        self.assert_chinese(",".join(rows[0]))
        teacher = self.success(self.core.export_timetable(
            str(self.fet), str(self.solution), "json", teacher="张老师"))
        self.assertEqual(teacher["row_count"], 2)
        self.assertIn("张老师", teacher["content"])
        self.assertNotIn("李老师", teacher["content"])
        self.assertEqual(len(json.loads(teacher["content"])), 2)
        students = self.success(self.core.export_timetable(
            str(self.fet), str(self.solution), "json", students="七年级一班"))
        self.assertEqual(students["row_count"], 1)
        self.assertIn("数学", students["content"])

    def test_parent_student_filter_includes_descendant_activities(self):
        result = self.success(self.core.export_timetable(
            str(self.fet), str(self.solution), "json", students="七年级"))
        self.assertEqual(result["row_count"], 3)

    def test_unknown_filters_invalid_format_and_types_are_rejected(self):
        for options in ({"format": "exe"}, {"format": []}, {"teacher": "不存在的老师"},
                        {"students": "不存在的班级"}, {"teacher": []}, {"students": True}):
            with self.subTest(options=options):
                self.rejected(self.core.export_timetable(str(self.fet), str(self.solution), **options))

    def test_export_preserves_findings_instead_of_claiming_full_validity(self):
        result = self.success(self.core.export_timetable(
            str(self.fet), str(self.directory / "冲突课表.xml"), "json"))
        self.assertFalse(result["verification"]["passed"], result)
        self.assertGreater(result["verification"]["issues_found"], 0)

    def test_csv_formula_injection_is_neutralized_but_json_preserves_data(self):
        for value in ("=1+1", "+SUM(A1)", "-1+1", "@危险", "\t=1+1", " =1+1"):
            with self.subTest(value=value):
                def alter(root):
                    root.find("Subjects_List/Subject/Name").text = value
                    root.find("Activities_List/Activity/Subject").text = value
                model = self.mutate(self.fet, alter)
                result = self.success(self.core.export_timetable(str(model), str(self.solution), "csv"))
                cells = [cell for row in csv.reader(io.StringIO(result["content"])) for cell in row]
                self.assertNotIn(value, cells)
                self.assertTrue(any(cell.startswith("'") and cell[1:].lstrip() == value.lstrip() for cell in cells), cells)
                exported = self.success(self.core.export_timetable(str(model), str(self.solution), "json"))
                self.assertIn(value.strip(), [str(v).strip() for row in json.loads(exported["content"]) for v in row.values()])

    def test_input_files_unchanged_after_all_read_only_operations(self):
        before = {path: path.read_bytes() for path in (self.fet, self.solution)}
        self.inspect()
        self.verify()
        self.core.export_timetable(str(self.fet), str(self.solution), "csv")
        self.assertEqual(before, {path: path.read_bytes() for path in before})


class FetAuditHostTests(FixtureCase):
    @classmethod
    def setUpClass(cls):
        try:
            from openjiuwen.core.common.logging.log_config import configure_log_config, get_log_config_snapshot
            config = get_log_config_snapshot()
            config["log_path"] = str(Path(tempfile.gettempdir()) / "fet-audit-test-host-logs")
            configure_log_config(config)
            from openjiuwen.core.foundation.tool import Tool
        except ModuleNotFoundError as exc:
            if not exc.name.startswith("openjiuwen"):
                raise
            raise unittest.SkipTest("Requires real WorkSwarm openJiuwen SDK") from exc
        with immutable_payload_import():
            cls.adapter = load_module("fet_audit_adapter_under_test", PAYLOAD / "tools/timetable_tools.py")
            cls.adapter._core()  # Resolve the lazy import without writing into source.
        cls.tool_type = Tool

    def test_real_sdk_tools_expose_localized_cards_and_invoke(self):
        cases = (
            (self.adapter.InspectFetTool, "inspect_fet", {"path": str(self.fet)}),
            (self.adapter.VerifyTimetableTool, "verify_fet_timetable", {"fet_path": str(self.fet), "solution_path": str(self.solution)}),
            (self.adapter.ExportTimetableTool, "export_fet_timetable", {"fet_path": str(self.fet), "solution_path": str(self.solution), "format": "json", "output_path": str(self.directory / "实际工具导出.json")}),
        )
        for klass, name, inputs in cases:
            with self.subTest(name=name):
                tool = klass()
                self.assertIsInstance(tool, self.tool_type)
                self.assertEqual(tool.card.name, name)
                self.assert_chinese(tool.card.description)
                for prop in tool.card.input_params["properties"].values():
                    self.assert_chinese(prop["description"])
                self.success(asyncio.run(tool.invoke(inputs)))

    def test_adapter_rejects_wrong_schema_and_unknown_operations(self):
        for operation, inputs in (
            ("inspect", None), ("inspect", []), ("inspect", {}),
            ("inspect", {"path": str(self.fet), "model": "paid"}),
            ("not_a_tool", {"fet_path": str(self.fet)}),
            ("verify", {"fet_path": str(self.fet)}),
        ):
            with self.subTest(operation=operation, inputs=inputs):
                self.rejected(self.adapter.run_tool(operation, inputs))

    def test_export_writes_exclusively_without_overwriting_source_or_existing_file(self):
        target = self.directory / "张老师课表.csv"
        inputs = {"fet_path": str(self.fet), "solution_path": str(self.solution),
                  "format": "csv", "teacher": "张老师", "output_path": str(target)}
        result = self.success(self.adapter.run_tool("export", inputs))
        self.assertTrue(target.is_file(), result)
        written = target.read_bytes()
        self.assertEqual(result["sha256"], hashlib.sha256(written).hexdigest())
        self.assertEqual(result["bytes"], len(written))
        self.assertEqual(result["content"].encode("utf-8"), written)
        self.assertIn("张老师", written.decode("utf-8-sig"))
        self.assertNotIn("李老师", written.decode("utf-8-sig"))
        self.rejected(self.adapter.run_tool("export", inputs))
        self.assertEqual(target.read_bytes(), written)
        original = self.fet.read_bytes()
        self.rejected(self.adapter.run_tool("export", {**inputs, "output_path": str(self.fet)}))
        self.assertEqual(self.fet.read_bytes(), original)

    def test_export_rejects_relative_symlink_and_missing_parent_destinations(self):
        target = self.directory / "原文件.csv"
        target.write_text("保留", encoding="utf-8")
        link = self.directory / "链接.csv"
        link.symlink_to(target)
        inputs = {"fet_path": str(self.fet), "solution_path": str(self.solution), "format": "csv"}
        for path in ("relative.csv", str(link), str(self.directory / "不存在的目录/课表.csv")):
            with self.subTest(path=path):
                self.rejected(self.adapter.run_tool("export", {**inputs, "output_path": path}))
        self.assertEqual(target.read_text(encoding="utf-8"), "保留")


class FetAuditCliTests(FixtureCase):
    def call(self, *args):
        return subprocess.run([sys.executable, "-B", str(PAYLOAD / "scripts/audit_cli.py"), *args],
                              capture_output=True, text=True, encoding="utf-8", timeout=10)

    def test_cli_reports_success_findings_and_errors_without_sdk(self):
        for args, code in ((("inspect", str(self.fet)), 0),
                           (("verify", str(self.fet), str(self.solution)), 0),
                           (("verify", str(self.fet), str(self.directory / "冲突课表.xml")), 1),
                           (("inspect", str(self.directory / "missing.fet")), 2)):
            result = self.call(*args)
            self.assertEqual(result.returncode, code, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["version"], VERSION)
            self.assertEqual(data["ok"], code != 2)

    def test_cli_chinese_help_and_bad_arguments(self):
        result = self.call("--help")
        self.assertEqual(result.returncode, 0)
        self.assert_chinese(result.stdout)
        result = self.call("solve", str(self.fet))
        self.assertEqual(result.returncode, 2)
        self.assert_chinese(json.loads(result.stdout)["error"]["message"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-demo-dir":
        print(json.dumps(make_demo_fixtures(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        unittest.main()
