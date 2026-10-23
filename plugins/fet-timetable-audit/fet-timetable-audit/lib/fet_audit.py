# -*- coding: utf-8 -*-
"""课表核验与导出：仅检查明确支持的项目，不求解课表。"""
# Adapted from nispa/fet-claude-skill, v1.2.1, commit
# beb2e1193665deb68b8f29d7617e7bb972573d95 (MIT; Copyright (c) 2026 nispa).
# Reused paths: skills/fet/scripts/{fet_common,fet_inspect,fet_timetable}.py.
# Original module headers are retained below as comments. The complete upstream
# license is bundled at licenses/fet-claude-skill/LICENSE.
# Modifications 2026-10-23: combine CLI algorithms into a structured Chinese API;
# bound and validate local XML, preserve duplicate-ID detection, apply inherited
# student unavailability consistently, report unsupported constraints, validate
# schedule references, and return safe CSV/JSON content without writing files.

import csv
import io
import json
import math
import os
import re
import stat
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "1.0.0"
MAX_BYTES = 8 * 1024 * 1024
MAX_NODES = 100000
MAX_DEPTH = 32
MAX_ACTIVITIES = 5000
MAX_ISSUES = 200
MAX_WORK = 200000


class AuditError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


class Issues:
    def __init__(self):
        self.items = []
        self.count = 0

    def add(self, code, message, **details):
        self.count += 1
        if len(self.items) < MAX_ISSUES:
            self.items.append(dict(code=code, message=message, **details))

    def result(self):
        return dict(passed=self.count == 0, issues_found=self.count,
                    issues=self.items, issues_truncated=self.count > len(self.items))


def _fail(code, message):
    raise AuditError(code, message)


def _read_local(path):
    if not isinstance(path, str) or not path or "\x00" in path or not Path(path).is_absolute():
        _fail("invalid_path", "请提供本机文件的绝对路径，不接受网址或相对路径。")
    p = Path(path)
    if ".." in p.parts:
        _fail("invalid_path", "文件路径不得包含上级目录跳转。")
    fd = None
    directory_fd = None
    try:
        # Open every component without following symlinks; descriptor-relative
        # traversal also closes the usual parent-directory replacement race.
        if os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW"):
            directory_fd = os.open(p.anchor, os.O_RDONLY | os.O_DIRECTORY)
            for component in p.parts[1:-1]:
                info = os.stat(component, dir_fd=directory_fd, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    _fail("symlink_path", "输入路径及其父目录不得是符号链接；请使用实际文件路径。")
                new_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                 dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = new_fd
            info = os.stat(p.name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                _fail("symlink_path", "输入文件不得是符号链接。")
            if not stat.S_ISREG(info.st_mode):
                _fail("invalid_file", "输入必须是普通文件，不能是目录、管道或设备。")
            fd = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory_fd)
        else:
            for component in [*reversed(p.parents), p]:
                if component.is_symlink():
                    _fail("symlink_path", "输入路径及其父目录不得是符号链接。")
            if not stat.S_ISREG(p.stat().st_mode):
                _fail("invalid_file", "输入必须是普通文件，不能是目录、管道或设备。")
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            _fail("invalid_file", "输入必须是普通文件。")
        if info.st_size > MAX_BYTES:
            _fail("resource_limit", "单个输入文件不能超过 8 MiB。")
        chunks, remaining = [], MAX_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > MAX_BYTES:
            _fail("resource_limit", "单个输入文件不能超过 8 MiB。")
        return content
    except OSError:
        _fail("invalid_file", "无法读取输入文件；请检查实际路径、文件类型和读取权限。")
    finally:
        if fd is not None:
            os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _xml(path, expected_root):
    raw = _read_local(path)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        _fail("invalid_encoding", "仅支持 UTF-8 编码的 XML 文件，请先转换编码。")
    if "\x00" in text:
        _fail("invalid_encoding", "仅支持 UTF-8 编码的 XML 文件。")
    declaration = re.match(r"\s*<\?xml[^>]*encoding\s*=\s*['\"]([^'\"]+)", text, re.I)
    if declaration and declaration.group(1).lower() not in ("utf-8", "utf8"):
        _fail("invalid_encoding", "XML 编码声明必须为 UTF-8。")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        _fail("xml_forbidden", "不接受 DTD 或实体声明；本工具不读取外部实体。")
    count = depth = 0
    try:
        parser = ET.iterparse(io.StringIO(text), events=("start", "end"))
        for event, element in parser:
            if event == "start":
                depth += 1
                count += 1
                if count > MAX_NODES or depth > MAX_DEPTH:
                    _fail("resource_limit", "XML 节点数量或嵌套深度超过限制。")
                if not isinstance(element.tag, str) or "}" in element.tag:
                    _fail("invalid_xml", "不支持带命名空间的 XML；请使用标准 FET 文件。")
            else:
                if len(element.text or "") > 4096 or any(len(v) > 4096 for v in element.attrib.values()):
                    _fail("resource_limit", "XML 单个文本字段或属性不能超过 4096 个字符。")
                depth -= 1
        root = parser.root
    except ET.ParseError:
        _fail("invalid_xml", "XML 格式无效或文件不完整。")
    if root.tag != expected_root:
        _fail("invalid_root", f"XML 根节点必须为 {expected_root}。")
    return root


def txt(el, tag, default=""):
    x = el.find(tag)
    return x.text.strip() if x is not None and x.text else default


def _single(el, tag, required=False, default=""):
    matches = el.findall(tag)
    if len(matches) > 1:
        _fail("duplicate_field", f"{el.tag} 中字段 {tag} 不得重复。")
    value = txt(el, tag, default)
    if len(value) > 256:
        _fail("resource_limit", f"字段 {tag} 不能超过 256 个字符。")
    if required and not value:
        _fail("missing_field", f"{el.tag} 缺少必填字段 {tag}。")
    return value


def _integer(value, label, minimum=0, maximum=1000000):
    if not re.fullmatch(r"[0-9]+", value) or len(value) > 9:
        _fail("invalid_integer", f"{label} 必须是有效的非负整数。")
    number = int(value)
    if not minimum <= number <= maximum:
        _fail("invalid_integer", f"{label} 必须在 {minimum} 至 {maximum} 之间。")
    return number


def _active(el):
    value = _single(el, "Active", default="true").lower()
    if value not in ("true", "false"):
        _fail("invalid_boolean", f"{el.tag} 的 Active 只能为 true 或 false。")
    return value == "true"


def _weight(el):
    value = _single(el, "Weight_Percentage", default="100")
    try:
        result = float(value)
    except ValueError:
        _fail("invalid_weight", "约束权重必须为 0 至 100 的数字。")
    if not math.isfinite(result) or not 0 <= result <= 100:
        _fail("invalid_weight", "约束权重必须为 0 至 100 的有限数字。")
    return result


# Original fet_common.py header:
# """Reading .fet files (FET 5.x-7.x) and *_activities.xml results. Standard library only."""
class Fet:
    def __init__(self, path):
        self.path = path
        self.root = _xml(path, "fet")
        r = self.root
        self.version = r.get("version", "未注明")
        self.institution = _single(r, "Institution_Name")
        self.days = self._names("Days_List", "Day", 366, required=True)
        self.hours = self._names("Hours_List", "Hour", 96, required=True)
        for container, count_tag, size in (("Days_List", "Number_of_Days", len(self.days)),
                                           ("Hours_List", "Number_of_Hours", len(self.hours))):
            stated = _single(self._container(container), count_tag)
            if stated and _integer(stated, count_tag) != size:
                _fail("invalid_grid", f"{count_tag} 与实际列表数量不一致。")
        self.subjects = self._names("Subjects_List", "Subject", 10000)
        self.teachers = self._names("Teachers_List", "Teacher", 10000)
        self.rooms = self._names("Rooms_List", "Room", 10000, optional=True)
        self.tags = self._names("Activity_Tags_List", "Activity_Tag", 10000, optional=True)
        self.students_kind, self.leaves = {}, {}
        students = self._container("Students_List")
        hierarchy_work = 0

        def define(name, kind, leaves):
            nonlocal hierarchy_work
            hierarchy_work += len(leaves)
            if hierarchy_work > 100000 or len(self.leaves) > 10000:
                _fail("resource_limit", "学生层级规模超过限制。")
            if name in self.leaves and (self.leaves[name] != leaves or self.students_kind[name] != kind):
                _fail("inconsistent_students", f"学生集合“{name}”存在不一致的重复层级定义。")
            self.students_kind[name] = kind
            self.leaves[name] = leaves

        # Year > Group > Subgroup; shared subgroups model intersecting groups.
        for year in students.findall("Year"):
            yn = _single(year, "Name", required=True)
            y_leaves = set()
            for group in year.findall("Group"):
                gn = _single(group, "Name", required=True)
                subs = set()
                for sub in group.findall("Subgroup"):
                    sn = _single(sub, "Name", required=True)
                    define(sn, "subgroup", {sn})
                    subs.add(sn)
                define(gn, "group", subs or {gn})
                y_leaves |= subs or {gn}
            define(yn, "year", y_leaves or {yn})

        self.activities = {}
        activity_elements = self._container("Activities_List").findall("Activity")
        if len(activity_elements) > MAX_ACTIVITIES:
            _fail("resource_limit", "课程活动数量不能超过 5000。")
        for a in activity_elements:
            aid = _single(a, "Id", required=True)
            _integer(aid, "活动 Id", minimum=1, maximum=999999999)
            aid = str(int(aid))
            if aid in self.activities:
                _fail("duplicate_activity_id", f"活动 Id {aid} 重复，无法可靠核验。")
            def values(tag):
                vals = [(el.text or "").strip() for el in a.findall(tag)]
                if any(not value or len(value) > 256 for value in vals) or len(set(vals)) != len(vals):
                    _fail("invalid_reference", f"活动 {aid} 的 {tag} 不得为空或重复。")
                return vals
            self.activities[aid] = dict(
                id=aid, teachers=values("Teacher"), subject=_single(a, "Subject", required=True),
                tags=values("Activity_Tag"), students=values("Students"),
                duration=_integer(_single(a, "Duration", required=True), "Duration", 1, 100000),
                total=_integer(_single(a, "Total_Duration", default="0"), "Total_Duration"),
                group=str(_integer(_single(a, "Activity_Group_Id", default="0"), "Activity_Group_Id", 0, 999999999)), active=_active(a))
        self.time_constraints = self._constraints(False)
        self.space_constraints = self._constraints(True)

    def _container(self, tag, optional=False):
        elements = self.root.findall(tag)
        if len(elements) > 1 or (not elements and not optional):
            _fail("invalid_structure", f"FET 文件必须包含且只能包含一个 {tag}。")
        return elements[0] if elements else ET.Element(tag)

    def _names(self, container, child, limit, required=False, optional=False):
        elements = self._container(container, optional).findall(child)
        names = [_single(el, "Name", required=True) for el in elements]
        if len(names) > limit:
            _fail("resource_limit", f"{container} 数量超过支持上限 {limit}。")
        if required and not names:
            _fail("invalid_grid", "日期与节次列表都必须非空。")
        if len(names) != len(set(names)):
            _fail("duplicate_name", f"{container} 中名称重复。")
        return names

    def _constraints(self, space):
        tag = "Space_Constraints_List" if space else "Time_Constraints_List"
        result = []
        for el in self._container(tag, optional=True):
            result.append(dict(element=el, type=el.tag, active=_active(el), weight=_weight(el)))
        return result

    def activity_leaves(self, activity):
        result = set()
        for name in activity["students"]:
            result.update(self.leaves.get(name, ()))
        return result

    def not_available(self):
        """Expand 100% student unavailability to shared leaves for every caller."""
        teachers, leaves = defaultdict(set), defaultdict(set)
        work = 0
        for c in self.time_constraints:
            if not c["active"] or c["weight"] != 100:
                continue
            el = c["element"]
            if c["type"] == "ConstraintTeacherNotAvailableTimes":
                names, target = [txt(el, "Teacher")], teachers
            elif c["type"] == "ConstraintStudentsSetNotAvailableTimes":
                names, target = self.leaves.get(txt(el, "Students"), ()), leaves
            else:
                continue
            slots = {(txt(na, "Day"), txt(na, "Hour")) for na in el.findall("Not_Available_Time")}
            slots = {s for s in slots if s[0] in self.days and s[1] in self.hours}
            work += len(names) * len(slots)
            if work > MAX_WORK:
                _fail("resource_limit", "不可用时段与学生集合的关联数量超过限制。")
            for name in names:
                target[name].update(slots)
        return teachers, leaves


def _coverage(f, operation="verify"):
    supported_types = {"ConstraintBasicCompulsoryTime", "ConstraintTeacherNotAvailableTimes",
                       "ConstraintStudentsSetNotAvailableTimes"}
    unsupported = Counter()
    ignored = Counter()
    space_ids = {id(c) for c in f.space_constraints}
    for c in f.time_constraints + f.space_constraints:
        if not c["active"]:
            ignored[c["type"]] += 1
        elif id(c) in space_ids or c["type"] not in supported_types or c["weight"] != 100:
            unsupported[(c["type"], c["weight"])] += 1
    supported = ["活动的教师、科目、学生与标签引用，以及约束的日期、节次、教师和学生引用",
                 "教师及学生末级集合工作量（扣除继承的 100% 不可用时段）"]
    if operation != "inspect":
        supported += ["缺排课程与超出每日节次", "教师及学生末级集合时间冲突",
                      "100% 教师及学生集合不可用时段（含继承）"]
    return dict(
        operation="静态检查" if operation == "inspect" else "给定课表核验", supported=supported,
        unsupported_constraints=[dict(type=kind, weight=weight, count=count)
                                 for (kind, weight), count in sorted(unsupported.items())],
        inactive_constraints=[dict(type=kind, count=count) for kind, count in sorted(ignored.items())],
        full_feasibility_checked=False,
        limitation="仅核验上述范围；不生成或修复课表，不检查教室冲突、软约束、间隔等其他约束，不能据此认定完整可行性。")


# Original fet_inspect.py headers:
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# fet_inspect.py — summary and static checks of a .fet file, BEFORE running FET.
# Reports: grid size, activities and hours, constraints by type, teacher and student workload
# compared with the available slots, and the errors that make FET reject the file (references
# to undeclared teachers/subjects/students, duplicate Ids, days/hours that don't exist in
# constraints). Exit 1 if it finds errors or certain infeasibilities.
def _inspect(f, issues):
    active = [a for a in f.activities.values() if a["active"]]
    slots = len(f.days) * len(f.hours)
    teachers, subjects = set(f.teachers), set(f.subjects)
    days, hours, tags = set(f.days), set(f.hours), set(f.tags)
    for a in f.activities.values():
        aid = a["id"]
        for t in a["teachers"]:
            if t not in teachers:
                issues.add("unknown_teacher", f"活动 {aid} 引用了未声明的教师“{t}”。", activity_id=aid)
        if a["subject"] not in subjects:
            issues.add("unknown_subject", f"活动 {aid} 引用了未声明的科目“{a['subject']}”。", activity_id=aid)
        for s in a["students"]:
            if s not in f.leaves:
                issues.add("unknown_students", f"活动 {aid} 引用了未声明的学生集合“{s}”。", activity_id=aid)
        for tag in a["tags"]:
            if tag not in tags:
                issues.add("unknown_activity_tag", f"活动 {aid} 引用了未声明的活动标签“{tag}”。", activity_id=aid)
        if a["duration"] > len(f.hours):
            issues.add("duration_overflow", f"活动 {aid} 持续节数超过一天的节次数量。", activity_id=aid)
        if a["total"] and a["total"] < a["duration"]:
            issues.add("invalid_total_duration", f"活动 {aid} 的总持续节数小于本活动持续节数。", activity_id=aid)
    for c in f.time_constraints + f.space_constraints:
        if not c["active"]:
            continue
        el, kind = c["element"], c["type"]
        for item in el.iter():
            value = (item.text or "").strip()
            if value and item.tag in ("Day", "Preferred_Day") and value not in days:
                issues.add("unknown_day", f"约束 {kind} 引用了未知日期“{value}”。")
            if value and item.tag in ("Hour", "Preferred_Hour") and value not in hours:
                issues.add("unknown_hour", f"约束 {kind} 引用了未知节次“{value}”。")
        for tag, known, code, label in (("Teacher", teachers, "unknown_teacher", "教师"),
                                       ("Teacher_Name", teachers, "unknown_teacher", "教师"),
                                       ("Students", f.leaves, "unknown_students", "学生集合"),
                                       ("Students_Name", f.leaves, "unknown_students", "学生集合")):
            name = _single(el, tag)
            if name and name not in known:
                issues.add(code, f"约束 {kind} 引用了未知{label}“{name}”。")
        if kind in ("ConstraintTeacherNotAvailableTimes", "ConstraintStudentsSetNotAvailableTimes"):
            _single(el, "Teacher" if kind.startswith("ConstraintTeacher") else "Students", required=True)
            for na in el.findall("Not_Available_Time"):
                _single(na, "Day", required=True)
                _single(na, "Hour", required=True)
            declared = _single(el, "Number_of_Not_Available_Times")
            if declared and _integer(declared, "Number_of_Not_Available_Times") != len(el.findall("Not_Available_Time")):
                issues.add("constraint_count_mismatch", f"约束 {kind} 的不可用时段数量与声明不一致。")
    na_t, na_s = f.not_available()
    load_t, load_s = defaultdict(int), defaultdict(int)
    work = 0
    for a in active:
        leaves = f.activity_leaves(a)
        work += len(leaves) + len(a["teachers"])
        if work > MAX_WORK:
            _fail("resource_limit", "活动与教师或学生集合的关联数量超过限制。")
        for t in a["teachers"]:
            load_t[t] += a["duration"]
        for leaf in leaves:
            load_s[leaf] += a["duration"]
    workload = {"teachers": [], "students": []}
    for kind, loads, unavailable in (("teachers", load_t, na_t), ("students", load_s, na_s)):
        for name, load in sorted(loads.items(), key=lambda item: (-item[1], item[0])):
            available = slots - len(unavailable.get(name, ()))
            workload[kind].append(dict(name=name, duration=load, available_slots=available,
                                       exceeds_available=load > available))
            if load > available:
                issues.add("workload_exceeds_availability", f"{'教师' if kind == 'teachers' else '学生集合'}“{name}”需 {load} 节，但仅有 {available} 个可用时段。")
    return dict(summary=dict(institution=f.institution, fet_version=f.version,
                             days=f.days, hours=f.hours, slots=slots, teachers=len(f.teachers),
                             subjects=len(f.subjects), students_sets=len(f.leaves), rooms=len(f.rooms),
                             activities=len(f.activities), active_activities=len(active),
                             total_duration=sum(a["duration"] for a in active)), workload=workload,
                students_hierarchy=[dict(name=name, kind=f.students_kind[name], leaves=sorted(leaves))
                                    for name, leaves in sorted(f.leaves.items())],
                constraints=dict(time=dict(Counter(c["type"] for c in f.time_constraints)),
                                 space=dict(Counter(c["type"] for c in f.space_constraints))))


def _solution(path):
    root = _xml(path, "Activities_Timetable")
    children = list(root)
    if any(c.tag != "Activity" for c in children):
        _fail("invalid_structure", "课表结果的根节点下只能包含 Activity。")
    if len(children) > MAX_ACTIVITIES:
        _fail("resource_limit", "课表结果的活动数量不能超过 5000。")
    sol = {}
    for a in children:
        aid = _single(a, "Id", required=True)
        _integer(aid, "结果活动 Id", 1, 999999999)
        aid = str(int(aid))
        if aid in sol:
            _fail("duplicate_solution_id", f"结果文件中的活动 Id {aid} 重复。")
        sol[aid] = (_single(a, "Day"), _single(a, "Hour"), _single(a, "Room"))
    return sol


# Original fet_timetable.py headers:
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# fet_timetable.py — read the timetable solved by FET, verify it and export it.
# Joins the .fet (teachers, subjects, students, durations) with *_activities.xml (day, hour, room).
# Verifies independently of FET:
#   - unplaced activities (empty <Day>: happens in "-highest" partial solutions);
#   - teacher and student overlaps (years/groups expanded into subgroups);
#   - lessons running past the end of the grid;
#   - violations of the 100% *NotAvailableTimes constraints found in the file.
# Exit 1 if it finds violations.
def _verify(f, sol, issues):
    di, hi = {d: i for i, d in enumerate(f.days)}, {h: i for i, h in enumerate(f.hours)}
    na_t, na_s = f.not_available()
    rows, unplaced = [], []
    occ_t, occ_s = {}, {}
    work = 0
    for aid in sol:
        if aid not in f.activities:
            issues.add("unknown_solution_activity", f"结果文件引用了未知活动 {aid}。", activity_id=aid)
        elif not f.activities[aid]["active"]:
            issues.add("inactive_activity", f"结果文件包含已停用活动 {aid}。", activity_id=aid)
    for aid, act in f.activities.items():
        if not act["active"]:
            continue
        day, hour, room = sol.get(aid, ("", "", ""))
        if not day or not hour:
            unplaced.append(aid)
            issues.add("unplaced_activity", f"活动 {aid} 尚未完整安排日期与节次。", activity_id=aid)
            continue
        invalid = False
        if day not in di:
            issues.add("unknown_day", f"活动 {aid} 使用了未知日期“{day}”。", activity_id=aid)
            invalid = True
        if hour not in hi:
            issues.add("unknown_hour", f"活动 {aid} 使用了未知节次“{hour}”。", activity_id=aid)
            invalid = True
        if invalid:
            continue
        h0 = hi[hour]
        hrs = f.hours[h0:min(h0 + act["duration"], len(f.hours))]
        if len(hrs) < act["duration"]:
            issues.add("duration_overflow", f"活动 {aid} 从“{hour}”开始后超出当日节次。", activity_id=aid)
        leaves = f.activity_leaves(act)
        work += len(hrs) * (len(act["teachers"]) + len(leaves))
        if work > MAX_WORK:
            _fail("resource_limit", "课表核验涉及的占用格数量超过 20 万。")
        for h in hrs:
            for kind, names, occupied, unavailable in (("teacher", act["teachers"], occ_t, na_t),
                                                      ("students", sorted(leaves), occ_s, na_s)):
                label = "教师" if kind == "teacher" else "学生集合"
                for name in names:
                    key = (name, day, h)
                    if key in occupied:
                        issues.add(kind + "_overlap", f"{label}“{name}”在 {day} {h} 的活动 {occupied[key]} 与 {aid} 重叠。",
                                   activity_ids=[occupied[key], aid], name=name, day=day, hour=h)
                    else:
                        occupied[key] = aid
                    if (day, h) in unavailable.get(name, ()):
                        issues.add(kind + "_unavailable", f"活动 {aid} 排在{label}“{name}”的不可用时段 {day} {h}。",
                                   activity_id=aid, name=name, day=day, hour=h)
        rows.append(dict(id=aid, day=day, day_index=di[day], start=hour, end=hrs[-1],
                         duration=act["duration"], subject=act["subject"], teachers=act["teachers"],
                         students=act["students"], room=room, _leaves=leaves))
    rows.sort(key=lambda r: (r["day_index"], hi[r["start"]], int(r["id"])))
    return rows, unplaced


def _public_row(row):
    return {key: value for key, value in row.items() if not key.startswith("_")}


def _result(f, issues, operation="verify", **fields):
    return dict(ok=True, version=VERSION,
                message="已完成限定范围核验；请查看问题清单与未检查的约束。",
                bounded_coverage=_coverage(f, operation), **issues.result(), **fields)


def _error(exc):
    return dict(ok=False, version=VERSION, error=dict(code=exc.code, message=exc.message))


def inspect_fet(path):
    """读取 FET 文件，检查引用、时段网格及工作量。"""
    try:
        f, issues = Fet(path), Issues()
        return _result(f, issues, operation="inspect", **_inspect(f, issues))
    except AuditError as exc:
        return _error(exc)


def verify_timetable(fet_path, solution_path):
    """核验给定课表的已支持约束；不进行完整可行性判断。"""
    try:
        f, issues = Fet(fet_path), Issues()
        static = _inspect(f, issues)
        rows, unplaced = _verify(f, _solution(solution_path), issues)
        return _result(f, issues, summary=static["summary"], workload=static["workload"],
                       placed_count=len(rows), unplaced=unplaced, rows=[_public_row(r) for r in rows])
    except AuditError as exc:
        return _error(exc)


def _csv_cell(value):
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def export_timetable(fet_path, solution_path, format="csv", teacher=None, students=None):
    """筛选后返回 CSV/JSON 字符串；不会修改输入文件或创建输出文件。"""
    try:
        if format not in ("csv", "json"):
            _fail("invalid_format", "导出格式只能为 csv 或 json。")
        f, issues = Fet(fet_path), Issues()
        _inspect(f, issues)
        if teacher is not None and (not isinstance(teacher, str) or teacher not in f.teachers):
            _fail("unknown_teacher", "教师筛选条件必须是 FET 文件中已声明的准确名称。")
        if students is not None and (not isinstance(students, str) or students not in f.leaves):
            _fail("unknown_students", "学生筛选条件必须是 FET 文件中已声明的准确名称。")
        rows, unplaced = _verify(f, _solution(solution_path), issues)
        selected = rows
        if teacher is not None:
            selected = [row for row in selected if teacher in row["teachers"]]
        if students is not None:
            selected = [row for row in selected if row["_leaves"] & f.leaves[students]]
        public = [_public_row(row) for row in selected]
        if format == "json":
            content = json.dumps(public, ensure_ascii=False, indent=2) + "\n"
        else:
            stream = io.StringIO(newline="")
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["活动编号", "日期", "开始节次", "结束节次（含）", "持续节数", "科目", "教师", "学生集合", "教室"])
            for row in selected:
                writer.writerow([_csv_cell(value) for value in
                                 (row["id"], row["day"], row["start"], row["end"], row["duration"], row["subject"],
                                  "、".join(row["teachers"]), "、".join(row["students"]), row["room"])])
            content = stream.getvalue()
        verification = _result(f, issues, placed_count=len(rows), unplaced=unplaced)
        return dict(ok=True, version=VERSION, format=format, row_count=len(public), content=content,
                    message="已生成筛选后的导出内容；导出成功不代表课表通过核验。", verification=verification,
                    csv_formula_protection="CSV 中可能触发公式的单元格已加前导单引号；JSON 保留原始文本。" if format == "csv" else None)
    except AuditError as exc:
        return _error(exc)
