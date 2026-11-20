"""依赖、离线登记与复工顺序分别生成并交接。"""
from contract import GATES, dependency_order, members, parser, read_case, require, run, same, stage, write_stage


def dependency_map(case):
    staff, flows = members(case)
    return {"order": dependency_order(flows),
            "flows": {key: {"name": flow["name"], "owner": flow["owner"], "needs": flow["needs"],
                            "source": flow["source"]} for key, flow in flows.items()},
            "staff": {key: person["name"] for key, person in staff.items()}}


def fallback_rules(case):
    staff, flows = members(case)
    return {"queue": "arrival-then-id", "staff_limits": {key: person["capacity"] for key, person in staff.items()},
            "workflow_limits": {key: flow["manual_limit"] for key, flow in flows.items()},
            "offline_fields": ["id", "flow", "arrival", "due", "revision"], "overflow": "defer"}


def restart_rules(case):
    _, flows = members(case)
    return {"gates": list(GATES), "order": dependency_order(flows),
            "workflows": {key: {"needs": flow["needs"], "startup": flow["startup"]} for key, flow in flows.items()},
            "snapshot_match": "same-id-and-revision", "conflict": "hold"}


def read_plans(args, case, source):
    mapping, mh = stage(args.map, "dependency-map", source)
    require(same(mapping, dependency_map(case)), "依赖图与原始案例不符")
    fallback, fh = stage(args.fallback, "fallback-plan", source, mapping=mh)
    require(same(fallback, fallback_rules(case)), "离线计划与原始约定不符")
    restart, rh = stage(args.restart, "restart-plan", source, mapping=mh, fallback=fh)
    require(same(restart, restart_rules(case)), "复工计划与原始约定不符")
    return fallback, restart, {"mapping": mh, "fallback": fh, "restart": rh}


def main():
    p = parser("生成依赖映射、离线登记计划或复工计划")
    p.add_argument("phase", choices=("map", "fallback", "restart"), help="选择角色所在阶段")
    p.add_argument("--map", help="依赖分析员的 JSON")
    p.add_argument("--fallback", help="离线作业设计员的 JSON")
    args = p.parse_args()
    case, source = read_case(args.input)
    if args.phase == "map":
        write_stage(args.output, "dependency-map", source, dependency_map(case))
    else:
        require(args.map, "须提供依赖分析员的交接文件")
        mapping, mh = stage(args.map, "dependency-map", source)
        require(same(mapping, dependency_map(case)), "依赖图与原始案例不符")
        if args.phase == "fallback":
            write_stage(args.output, "fallback-plan", source, fallback_rules(case), mapping=mh)
        else:
            require(args.fallback, "须提供离线作业设计员的交接文件")
            fallback, fh = stage(args.fallback, "fallback-plan", source, mapping=mh)
            require(same(fallback, fallback_rules(case)), "离线计划与原始约定不符")
            write_stage(args.output, "restart-plan", source, restart_rules(case), mapping=mh, fallback=fh)
    print("已保存阶段计划，输入与上游摘要已绑定。")


if __name__ == "__main__":
    raise SystemExit(run(main))
