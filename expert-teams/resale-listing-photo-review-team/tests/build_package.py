"""Run the maintained Expert Team packer against this asset."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
helper = root.parent / "laundry-load-review-team/tests/build_package.py"
spec = importlib.util.spec_from_file_location("expert_team_packaging", helper)
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)
packaging.TEAM_DIR = root
packaging.SLUG = root.name
packaging.PAYLOAD = root / root.name
packaging.OUTPUT_ROOT = root

if __name__ == "__main__":
    packaging.main()
