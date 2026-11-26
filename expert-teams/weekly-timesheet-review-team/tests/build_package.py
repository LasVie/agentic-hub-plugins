"""Use the maintained repository Expert Team archive checks for this asset."""
import importlib.util
from pathlib import Path

asset = Path(__file__).resolve().parents[1]
tool = asset.parent / "laundry-load-review-team/tests/build_package.py"
spec = importlib.util.spec_from_file_location("expert_team_packaging", tool)
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)
packaging.TEAM_DIR = asset
packaging.SLUG = asset.name
packaging.PAYLOAD = asset / asset.name
packaging.OUTPUT_ROOT = asset

if __name__ == "__main__":
    packaging.main()
