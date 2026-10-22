"""Offline functional tests for Deckaura Tarot and its real openJiuwen adapter.

Run with the WorkSwarm Python environment and Node.js >=18 on PATH. Set
DECKAURA_PAYLOAD to an extracted inner plugin directory to test a release ZIP.
No model credentials, network calls, or substitute host Tool classes are used.
Generic repository CI skips this suite if the host SDK or Node.js is absent.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    from openjiuwen.core.common.logging.log_config import (
        configure_log_config, get_log_config_snapshot,
    )

    host_log_config = get_log_config_snapshot()
    host_log_config["log_path"] = os.environ.get(
        "DECKAURA_TEST_LOG_DIR", str(Path(tempfile.gettempdir()) / "deckaura-test-host-logs")
    )
    configure_log_config(host_log_config)
    from openjiuwen.core.foundation.tool import Tool
except ModuleNotFoundError as exc:
    if not exc.name.startswith("openjiuwen"):
        raise
    Tool = None


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get(
    "DECKAURA_PAYLOAD", str(ROOT / "plugins/deckaura-tarot/deckaura-tarot")
)).resolve()


def load_adapter(payload: Path):
    spec = importlib.util.spec_from_file_location(
        "deckaura_tarot_under_test", payload / "tools/tarot_tool.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = load_adapter(PAYLOAD) if Tool is not None else None
SCRIPT = PAYLOAD / "skills/tarot-reading/scripts/tarot.mjs"
DECK = PAYLOAD / "skills/tarot-reading/assets/deck.json"
POSITIONS = {
    "daily": ["Theme for reflection"],
    "three-card": ["Past or background", "Present dynamic", "Future tendency"],
    "decision": ["Situation", "Option A", "Option B", "What to consider", "Grounded next step"],
    "relationship": ["You", "Other person or perceived dynamic", "Connection", "Strength", "Challenge", "Constructive next step"],
    "celtic-cross": [
        "Present situation", "Challenge or crossing influence", "Foundation",
        "Recent past", "Conscious aim or possibility", "Near-term direction",
        "Your stance", "Environment or external influences", "Hopes and fears", "Outcome tendency",
    ],
    "yes-no": ["Symbolic tendency"],
}


@unittest.skipUnless(Tool is not None, "Requires the actual WorkSwarm openJiuwen SDK")
@unittest.skipUnless(shutil.which("node"), "Requires Node.js >=18 on PATH")
class TarotFunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if not cls.node:
            raise RuntimeError("Node.js >=18 is required; this is not a skipped test suite.")
        version = subprocess.run(
            [cls.node, "--version"], check=True, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        if int(version.lstrip("v").split(".")[0]) < 18:
            raise RuntimeError(f"Node.js >=18 is required, found {version}.")
        cls.deck = json.loads(DECK.read_text(encoding="utf-8"))
        cls.cards = {card["card_name"]: card for card in cls.deck["cards"]}

    def run_ok(self, inputs):
        result = ADAPTER.run_tarot(inputs)
        self.assertTrue(result.get("ok"), result)
        return result

    def assert_invalid(self, inputs):
        result = ADAPTER.run_tarot(inputs)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_input", result)

    def assert_cards(self, cards):
        self.assertEqual(len({card["card_name"] for card in cards}), len(cards))
        for card in cards:
            original = self.cards[card["card_name"]]
            self.assertIn(card["orientation"], ("upright", "reversed"))
            self.assertEqual(card["meaning"], original[f"{card['orientation']}_meaning"])
            self.assertEqual(card["guide_url"], original["guide_url"])
            self.assertTrue(card["position"])

    def test_dataset_has_78_unique_cards_and_urls(self):
        self.assertEqual(self.deck["count"], 78)
        self.assertEqual(len(self.cards), 78)
        self.assertEqual(len({card["guide_url"] for card in self.cards.values()}), 78)
        for card in self.cards.values():
            for field in ("card_name", "upright_meaning", "reversed_meaning", "guide_url"):
                self.assertIsInstance(card[field], str)
                self.assertTrue(card[field].strip())

    def test_validate_cli_output_matches_bundled_bytes(self):
        result = self.run_ok({"action": "validate"})
        self.assertEqual(result["count"], 78)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["sha256"], hashlib.sha256(DECK.read_bytes()).hexdigest())

    def test_lookup_aliases_and_unicode_normalization(self):
        for alias in ("The Star", "star", "  STAR  ", "thé stár"):
            with self.subTest(alias=alias):
                card = self.run_ok({"action": "lookup", "card": alias})["card"]
                self.assertEqual(card["card_name"], "The Star")
                self.assertEqual(card["orientation"], "upright")
                self.assertEqual(card["meaning"], "Hope, renewal, spirituality, inspiration")
                self.assertEqual(card["position"], "Lookup")

    def test_lookup_reversed_meaning(self):
        card = self.run_ok({"action": "lookup", "card": "The Star", "orientation": "reversed"})["card"]
        self.assertEqual(card["orientation"], "reversed")
        self.assertEqual(card["meaning"], self.cards["The Star"]["reversed_meaning"])
        self.assertNotEqual(card["meaning"], self.cards["The Star"]["upright_meaning"])

    def test_unknown_card_returns_bounded_suggestions(self):
        result = ADAPTER.run_tarot({"action": "lookup", "card": "cups"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "operation_failed")
        suggestions = result["error"]["suggestions"]
        self.assertGreater(len(suggestions), 0)
        self.assertLessEqual(len(suggestions), 10)
        self.assertTrue(all("Cups" in name and name in self.cards for name in suggestions))
        unknown = ADAPTER.run_tarot({"action": "lookup", "card": "nonexistent zz card"})
        self.assertEqual(unknown["error"]["suggestions"], [])

    def test_full_deck_seeded_draw_is_reproducible_and_unique(self):
        request = {"action": "draw", "count": 78, "seed": "local-functional-suite", "reversals": True}
        first = self.run_ok(request)
        self.assertEqual(first, self.run_ok(request))
        self.assertEqual({card["card_name"] for card in first["cards"]}, set(self.cards))
        self.assertEqual([card["position"] for card in first["cards"]], [f"Card {i}" for i in range(1, 79)])
        self.assertEqual({card["orientation"] for card in first["cards"]}, {"upright", "reversed"})
        self.assert_cards(first["cards"])

    def test_generated_seed_replays_exact_draw(self):
        first = self.run_ok({"action": "draw", "count": 8})
        self.assertRegex(first["seed"], r"^[0-9a-f]{32}$")
        replay = self.run_ok({"action": "draw", "count": 8, "seed": first["seed"]})
        self.assertEqual(first, replay)

    def test_reversals_false_keeps_all_78_upright(self):
        result = self.run_ok({"action": "draw", "count": 78, "seed": "no-reversals", "reversals": False})
        self.assertFalse(result["reversals"])
        self.assertEqual({card["orientation"] for card in result["cards"]}, {"upright"})
        self.assert_cards(result["cards"])

    def test_draw_defaults_to_one_card(self):
        self.assertEqual(len(self.run_ok({"action": "draw", "seed": "single"})["cards"]), 1)

    def test_all_six_spreads_have_correct_unique_positions(self):
        for name, positions in POSITIONS.items():
            with self.subTest(spread=name):
                result = self.run_ok({"action": "spread", "spread": name, "seed": f"spread-{name}"})
                self.assertEqual(result["spread"], name)
                self.assertEqual([card["position"] for card in result["cards"]], positions)
                self.assert_cards(result["cards"])

    def test_invalid_actions_and_non_object_inputs(self):
        for request in (None, [], "draw", 1, {}, {"action": None}, {"action": "execute"}, {"action": []}):
            with self.subTest(request=request):
                self.assert_invalid(request)

    def test_action_specific_unknown_fields_are_rejected(self):
        requests = (
            {"action": "lookup", "card": "Star", "seed": "irrelevant"},
            {"action": "draw", "card": "Star"},
            {"action": "spread", "spread": "daily", "count": 4},
            {"action": "validate", "path": "/tmp/other-deck.json"},
        )
        for request in requests:
            with self.subTest(request=request):
                self.assert_invalid(request)

    def test_invalid_card_names(self):
        for card in (None, "", "  ", 1, [], "x" * 101, "--help", "  --seed", "Star\x00"):
            with self.subTest(card=card):
                self.assert_invalid({"action": "lookup", "card": card})

    def test_invalid_orientation(self):
        for orientation in (None, "up", "REVERSED", 0, True, []):
            with self.subTest(orientation=orientation):
                self.assert_invalid({"action": "lookup", "card": "Star", "orientation": orientation})

    def test_invalid_count_type_and_bounds(self):
        for count in (True, False, 1.0, 2.5, 0, -1, 79, "3", None, []):
            with self.subTest(count=count):
                self.assert_invalid({"action": "draw", "count": count})

    def test_invalid_spread_names(self):
        for spread in (None, "", "Daily", "not-a-spread", 1, []):
            with self.subTest(spread=spread):
                self.assert_invalid({"action": "spread", "spread": spread})

    def test_invalid_reversal_types(self):
        for action in ("draw", "spread"):
            for value in ("true", "false", 0, 1, None, []):
                request = {"action": action, "reversals": value}
                if action == "spread":
                    request["spread"] = "daily"
                with self.subTest(action=action, reversals=value):
                    self.assert_invalid(request)

    def test_invalid_seeds(self):
        for seed in (None, "", 0, True, [], "--help", "--seed other", "a\x00b", "x" * 257):
            with self.subTest(seed=seed):
                self.assert_invalid({"action": "draw", "seed": seed})

    def test_valid_seed_boundaries_and_literal_shell_characters(self):
        for seed in ("x", "x" * 256, "literal; $(not-a-command) 'quoted' & value"):
            with self.subTest(seed=seed):
                result = self.run_ok({"action": "draw", "seed": seed})
                self.assertEqual(result["seed"], seed)
                self.assertEqual(len(result["cards"]), 1)

    def test_missing_node_has_actionable_error(self):
        with patch.object(ADAPTER.shutil, "which", return_value=None):
            result = ADAPTER.run_tarot({"action": "validate"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "missing_node")
        self.assertIn("PATH", result["error"]["message"])

    def test_timeout_is_bounded_and_reported(self):
        with patch.object(ADAPTER.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 10)) as run:
            result = ADAPTER.run_tarot({"action": "validate"})
        self.assertEqual(result["error"]["code"], "timeout")
        self.assertEqual(run.call_args.kwargs["timeout"], 10)
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_actual_node_cli_matches_host_draw(self):
        result = subprocess.run(
            [self.node, str(SCRIPT), "draw", "--count", "8", "--seed", "cli-parity", "--reversals", "false"],
            capture_output=True, text=True, check=True, timeout=10, cwd=tempfile.gettempdir(),
        )
        expected = json.loads(result.stdout)
        self.assertEqual(self.run_ok({"action": "draw", "count": 8, "seed": "cli-parity", "reversals": False}), {"ok": True, **expected})

    def test_actual_node_cli_rejects_invalid_count(self):
        result = subprocess.run(
            [self.node, str(SCRIPT), "draw", "--count", "79"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("1 to 78", json.loads(result.stderr)["error"])

    def test_native_tool_schema_and_async_invoke(self):
        tool = ADAPTER.TarotTool()
        self.assertIsInstance(tool, Tool)
        self.assertEqual(tool.card.name, "deckaura_tarot")
        self.assertEqual(tool.card.input_params["required"], ["action"])
        request = {"action": "spread", "spread": "three-card", "seed": "native-invoke"}
        self.assertEqual(asyncio.run(tool.invoke(request)), self.run_ok(request))

    def test_native_tool_async_stream_yields_one_complete_result(self):
        request = {"action": "lookup", "card": "Star", "orientation": "reversed"}

        async def collect():
            return [item async for item in ADAPTER.TarotTool().stream(request)]

        self.assertEqual(asyncio.run(collect()), [self.run_ok(request)])

    def test_relocated_payload_runs_outside_repository(self):
        with tempfile.TemporaryDirectory(prefix="deckaura-relocation-") as directory:
            destination = Path(directory).resolve() / "installed plugin"
            shutil.copytree(PAYLOAD, destination, ignore=shutil.ignore_patterns("__pycache__"))
            relocated = load_adapter(destination)
            self.assertEqual(relocated.SCRIPT, destination / "skills/tarot-reading/scripts/tarot.mjs")
            request = {"action": "spread", "spread": "celtic-cross", "seed": "relocated"}
            self.assertEqual(relocated.run_tarot(request), self.run_ok(request))


if __name__ == "__main__":
    unittest.main(verbosity=2)
