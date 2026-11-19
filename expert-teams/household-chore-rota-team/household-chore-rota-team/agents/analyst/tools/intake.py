"""核对用户已约定的结构化家务资料，不代替自然语言确认。"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/rota-evidence/scripts"))
from contract import ChineseParser, VERSION, cli, digest, new_dir, read_json, validate_case, write_json


def run() -> int:
    parser = ChineseParser(description="核对已约定的一周家务输入；输出目录必须尚不存在")
    parser.add_argument("--input", required=True, type=Path, help="案例JSON的绝对路径")
    parser.add_argument("--output", required=True, type=Path, help="新的梳理报告目录")
    args = parser.parse_args()
    case, source = read_json(args.input)
    validate_case(case)
    result = {"schema_version": 1, "kind": "rota-intake/v1", "version": VERSION,
              "source_sha256": source, "case_sha256": digest(case), "case": case,
              "summary": {"participants": len(case["participants"]), "occurrences": len(case["duties"]),
                          "total_minutes": sum(d["minutes"] for d in case["duties"]),
                          "boundary": "只核对结构与约定数据；实际来源含义和遗漏仍需梳理员对照用户原话"}}
    dest = new_dir(args.output)
    write_json(dest / "intake.json", result)
    print(json.dumps({"ok": True, "报告": str(dest / "intake.json"), "案例摘要": result["summary"], "case_sha256": result["case_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    cli(run)
