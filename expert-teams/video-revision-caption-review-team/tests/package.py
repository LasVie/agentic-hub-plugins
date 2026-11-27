"""Package the caption review team through the maintained AgentGroup harness."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ASSET = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    spec = spec_from_file_location(
        "order_team_packager", ASSET.parent / "online-order-payment-review-team/tests/package.py"
    )
    packager = module_from_spec(spec)
    spec.loader.exec_module(packager)
    packager.ASSET = ASSET
    packager.SLUG = ASSET.name
    packager.main()
