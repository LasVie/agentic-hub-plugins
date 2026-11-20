"""从已确认的原始输入生成梳理回执。"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/meeting-evidence/scripts"))
from contract import ChineseParser, cli, input_state, intake, write


def main():
    p = ChineseParser(usage="intake.py --input 案例.json --output 新回执.json", description="检查参会窗口与时区数据")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    case, _, identity = input_state(args.input)
    write(args.output, intake(identity))
    print(f"已检查{len(case.people)}位参会者、{len(case.slots)}个候选及{case.weeks}周；回执已写入")


if __name__ == "__main__":
    cli(main)
