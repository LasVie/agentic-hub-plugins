"""Offline tests using known synthetic signals and the actual Node/host tool.

Run ``python -m unittest discover -s tests -p test_dsh_ears_prosody.py -v``
with Node.js >=20 on PATH. Set PROSODY_PAYLOAD to an extracted inner plugin
directory to test the release bytes. Adapter tests require the real openJiuwen
SDK; no model, network service, recording device or substitute Tool is used.
Set PROSODY_BASELINE_ZIP to the preserved 1.0.0 canonical ZIP to additionally
compare measurements across localization. Generic CI skips only that optional
historical comparison; the synthetic functional tests do not depend on it.
``python tests/test_dsh_ears_prosody.py --write-demo-dir /absolute/directory``
creates synthetic manual-testing inputs outside the runtime package.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get(
    "PROSODY_PAYLOAD", str(ROOT / "plugins/dsh-ears-prosody/dsh-ears-prosody")
)).resolve()
SCRIPT = PAYLOAD / "scripts/analyze.mjs"
NODE = shutil.which("node")
SAMPLE_RATE = 16000
VERSION = "1.0.1"
DEMO_NAME = "三段音高示例.wav"
SILENCE_NAME = "静音示例.wav"
BASELINE_ZIP = Path(os.environ["PROSODY_BASELINE_ZIP"]).resolve() if os.environ.get("PROSODY_BASELINE_ZIP") else None
BASELINE_SHA256 = "819341f0c0000225beb197ef04dd0c96982187bbfec670c7658b45716f302008"


def tone(seconds, frequency=220, amplitude=0.4, rate=SAMPLE_RATE, end_hz=None):
    """A sine wave or linear frequency sweep, without using plugin code."""
    slope = 0 if end_hz is None else (end_hz - frequency) / seconds
    return [amplitude * math.sin(2 * math.pi * (
        frequency * (i / rate) + slope * (i / rate) ** 2 / 2
    )) for i in range(round(seconds * rate))]


def quiet(seconds, rate=SAMPLE_RATE):
    return [0.0] * round(seconds * rate)


def riff_chunk(name, payload):
    return name + struct.pack("<I", len(payload)) + payload + b"\0" * (len(payload) % 2)


def riff_wave(chunks):
    body = b"WAVE" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def wav_bytes(samples, *, rate=SAMPLE_RATE, channels=1, bits=16,
              floating=False, extensible=False, extra_chunks=()):
    """Encode mono samples into independently constructed RIFF/WAVE fixtures.

    Stereo repeats each sample in both channels, so the expected downmix is
    unambiguous. Extensible fixtures use the standard PCM/IEEE_FLOAT subtype.
    """
    encoded = bytearray()
    for sample in samples:
        if floating:
            value = struct.pack("<f" if bits == 32 else "<d", sample)
        elif bits == 8:
            value = bytes([max(0, min(255, round(sample * 127 + 128)))])
        else:
            limit = 1 << (bits - 1)
            integer = max(-limit, min(limit - 1, round(sample * (limit - 1))))
            value = integer.to_bytes(bits // 8, "little", signed=True)
        encoded.extend(value * channels)
    block = channels * bits // 8
    tag = 3 if floating else 1
    fmt = struct.pack("<HHIIHH", 0xFFFE if extensible else tag, channels,
                      rate, rate * block, block, bits)
    if extensible:
        guid = struct.pack("<IHH", tag, 0, 0x0010) + bytes.fromhex("800000aa00389b71")
        fmt += struct.pack("<HHI", 22, bits, 4 if channels == 1 else 3) + guid
    return riff_wave([riff_chunk(b"fmt ", fmt), *extra_chunks,
                      riff_chunk(b"data", bytes(encoded))])


def make_demo_fixtures(destination):
    """Write a five-second signal with three tones and two 400 ms pauses."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    demo = (quiet(0.3) + tone(1.2, 180, 0.25) + quiet(0.4)
            + tone(1.2, 220, 0.5) + quiet(0.4) + tone(1.2, 260, 0.25)
            + quiet(0.3))
    files = {
        DEMO_NAME: wav_bytes(demo),
        SILENCE_NAME: wav_bytes(quiet(1.0)),
    }
    for name, contents in files.items():
        (destination / name).write_bytes(contents)
    return {
        "directory": str(destination),
        DEMO_NAME: {
            "duration_seconds": 5.0, "tone_hz": [180, 220, 260],
            "tone_seconds_each": 1.2, "internal_pause_seconds": [0.4, 0.4],
            "leading_and_trailing_silence_seconds": 0.3,
            "description": "人工合成的三个音调，不是真人语音录音。",
        },
        SILENCE_NAME: {"duration_seconds": 1.0, "expected": "没有活动片段或可测音高。"},
    }


class FixtureTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="prosody-functional-")
        self.directory = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)

    def write(self, name, contents):
        path = self.directory / name
        path.write_bytes(contents)
        return path

    def signal(self, samples, name="signal.wav", **options):
        return self.write(name, wav_bytes(samples, **options))

    def assert_chinese(self, text):
        self.assertIsInstance(text, str)
        self.assertRegex(text, r"[\u4e00-\u9fff]", text)
        self.assertNotIn("\ufffd", text)


@unittest.skipUnless(NODE, "Requires Node.js >=20 on PATH")
class ProsodyCliTests(FixtureTestCase):
    @classmethod
    def setUpClass(cls):
        major = int(subprocess.run([NODE, "--version"], check=True, capture_output=True,
                                   text=True, timeout=10).stdout.lstrip("v").split(".")[0])
        if major < 20:
            raise RuntimeError(f"Node.js >=20 required, found major version {major}")

    def invoke(self, *arguments):
        process = subprocess.run([NODE, str(SCRIPT), *map(str, arguments)],
                                 capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=35,
                                 cwd=self.directory)
        try:
            result = json.loads(process.stdout)
        except json.JSONDecodeError:
            self.fail(f"CLI must return JSON: {process.stdout!r}; stderr={process.stderr!r}")
        self.assertIsInstance(result, dict)
        self.assertEqual(process.stderr, "", process.stderr)
        return process, result

    def ok(self, path):
        process, result = self.invoke(path)
        self.assertEqual(process.returncode, 0, result)
        self.assertIs(result.get("ok"), True, result)
        self.assertEqual(result["version"], VERSION)
        return result

    def rejected(self, *arguments):
        process, result = self.invoke(*arguments)
        self.assertNotEqual(process.returncode, 0, result)
        self.assertIs(result.get("ok"), False, result)
        self.assertIsInstance(result["error"]["code"], str)
        self.assertRegex(result["error"]["code"], r"^[A-Z0-9_]+$")
        self.assertEqual(result["version"], VERSION)
        self.assert_chinese(result["error"]["message"])
        self.assertNotIn("at file:", result["error"]["message"])
        return result

    def test_known_pitch_and_audio_metadata(self):
        result = self.ok(self.signal(quiet(0.25) + tone(1.5) + quiet(0.25)))
        self.assertAlmostEqual(result["audio"]["durationSec"], 2.0, places=3)
        self.assertEqual(result["audio"]["sampleRate"], SAMPLE_RATE)
        self.assertEqual(result["audio"]["channels"], 1)
        self.assertEqual(result["audio"]["bitsPerSample"], 16)
        self.assertEqual(result["audio"]["frames"], 32000)
        self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)
        self.assertGreater(result["pitch"]["voicedFrames"], 30)
        self.assertGreater(result["activity"]["activeSec"], 1.25)
        self.assertLess(result["activity"]["activeSec"], 1.7)

    def test_continuous_tone_without_silence_is_not_discarded(self):
        result = self.ok(self.signal(tone(1.0, 180)))
        self.assertAlmostEqual(result["pitch"]["meanHz"], 180, delta=10)
        self.assertGreater(result["activity"]["activeRatio"], 0.85)

    def test_rising_and_falling_pitch_contours(self):
        for first, last, label, sign in ((120, 260, "rising", 1),
                                       (260, 120, "falling", -1)):
            with self.subTest(contour=label):
                result = self.ok(self.signal(quiet(0.2) + tone(2.0, first, end_hz=last)
                                             + quiet(0.2)))
                contours = result["pitch"]["contours"]
                self.assertTrue(contours)
                strongest = max(contours, key=lambda item: item["endSec"] - item["startSec"])
                self.assertEqual(strongest["contour"], label)
                self.assertGreater(sign * strongest["slopeHzPerSec"], 30)

    def test_three_segments_and_two_measured_pauses(self):
        make_demo_fixtures(self.directory)
        result = self.ok(self.directory / DEMO_NAME)
        self.assertEqual(result["activity"]["segmentCount"], 3)
        self.assertEqual(result["pause"]["count"], 2)
        for duration in result["pause"]["durationsMs"]:
            self.assertAlmostEqual(duration, 400, delta=90)
        self.assertAlmostEqual(result["pause"]["leadingSilenceMs"], 300, delta=90)
        self.assertAlmostEqual(result["pause"]["trailingSilenceMs"], 300, delta=90)
        self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=15)

    def test_amplitude_change_has_measurable_energy_range(self):
        for silence_seconds in (0, 0.2):
            with self.subTest(silence_seconds=silence_seconds):
                samples = (quiet(silence_seconds) + tone(0.8, amplitude=0.08)
                           + tone(0.8, amplitude=0.64) + quiet(silence_seconds))
                result = self.ok(self.signal(samples))
                self.assertGreater(result["energy"]["rangeDb"], 12)
                # peakDb is explicitly the maximum frame RMS, not sample peak level.
                self.assertAlmostEqual(result["energy"]["peakDb"], 20 * math.log10(0.64 / math.sqrt(2)), delta=0.3)
                self.assertLess(result["energy"]["rmsDb"], result["energy"]["peakDb"])

    def test_silence_has_no_activity_pitch_or_pacing(self):
        result = self.ok(self.signal(quiet(1.0)))
        self.assertEqual(result["activity"]["segmentCount"], 0)
        self.assertEqual(result["activity"]["activeSec"], 0)
        self.assertIsNone(result["pitch"]["meanHz"])
        self.assertEqual(result["pitch"]["voicedFrames"], 0)
        self.assertEqual(result["tempo"]["energyPeaks"], 0)
        self.assertTrue(result["limitations"])

    def test_white_noise_is_not_reported_as_confident_periodic_voice(self):
        rng = random.Random(20261022)
        noise = [rng.uniform(-0.4, 0.4) for _ in range(SAMPLE_RATE)]
        result = self.ok(self.signal(quiet(0.2) + noise + quiet(0.2)))
        self.assertLessEqual(result["pitch"]["voicedFrames"], 5)
        self.assertTrue(result["limitations"])

    def test_pacing_is_an_explicitly_limited_energy_proxy(self):
        samples = quiet(0.2)
        for _ in range(5):
            pulse = tone(0.24, amplitude=0.35)
            samples += [value * math.sin(math.pi * i / (len(pulse) - 1)) ** 2
                        for i, value in enumerate(pulse)] + quiet(0.16)
        result = self.ok(self.signal(samples + quiet(0.2)))
        self.assertGreater(result["tempo"]["energyPeaks"], 0)
        description = result["tempo"]["definition"].lower()
        self.assertTrue(any(term in description for term in ("能量", "rms", "均方根")), description)
        self.assertTrue("不是" in description or "不等于" in description, description)
        self.assert_chinese(description)
        self.assertTrue(result["limitations"])
        self.assertNotIn("emotion", result)
        self.assertNotIn("transcript", result)

    def test_pcm_float_and_extensible_formats(self):
        cases = [(bits, False, False) for bits in (8, 16, 24, 32)]
        cases += [(bits, True, False) for bits in (32, 64)]
        cases += [(16, False, True), (32, True, True)]
        for bits, floating, extensible in cases:
            with self.subTest(bits=bits, floating=floating, extensible=extensible):
                path = self.signal(quiet(0.15) + tone(0.6) + quiet(0.15),
                                   bits=bits, floating=floating, extensible=extensible)
                result = self.ok(path)
                self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)
                self.assertEqual(result["audio"]["bitsPerSample"], bits)

    def test_mono_and_stereo_at_supported_rate_extremes(self):
        for rate, channels in ((8000, 1), (44100, 2), (48000, 2)):
            with self.subTest(rate=rate, channels=channels):
                path = self.signal(quiet(0.15, rate) + tone(0.6, rate=rate) + quiet(0.15, rate),
                                   rate=rate, channels=channels)
                result = self.ok(path)
                self.assertEqual(result["audio"]["sampleRate"], rate)
                self.assertEqual(result["audio"]["channels"], channels)
                self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)

    def test_unknown_odd_sized_chunk_is_skipped_with_padding(self):
        result = self.ok(self.signal(tone(0.5), extra_chunks=[riff_chunk(b"JUNK", b"abc")]))
        self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)

    def test_downsampling_does_not_alias_high_tone_into_voice_pitch(self):
        samples = quiet(0.15, 48000) + tone(0.6, 7800, rate=48000) + quiet(0.15, 48000)
        result = self.ok(self.signal(samples, rate=48000))
        self.assertLessEqual(result["pitch"]["voicedFrames"], 2)

    def test_repeatable_read_only_operation_and_unicode_path(self):
        path = self.signal(tone(0.6), name="中文 练习 $(touch injected).wav")
        original = hashlib.sha256(path.read_bytes()).hexdigest()
        path.chmod(0o444)
        first = self.ok(path)
        self.assertEqual(first, self.ok(path))
        self.assertEqual(original, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(set(self.directory.iterdir()), {path})

    def test_duration_boundaries(self):
        self.ok(self.signal(quiet(0.1)))
        self.rejected(self.signal(quiet(0.099)))
        self.rejected(self.signal(quiet(60.01, 8000), rate=8000))
        result = self.ok(self.signal(quiet(60, 8000), rate=8000))
        self.assertEqual(result["audio"]["durationSec"], 60)

    def test_long_voiced_input_completes_within_cli_deadline(self):
        result = self.ok(self.signal(tone(60, rate=8000), rate=8000))
        self.assertEqual(result["audio"]["durationSec"], 60)
        self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)

    def test_cli_requires_exactly_one_absolute_local_regular_file(self):
        path = self.signal(quiet(0.1))
        link = self.directory / "linked.wav"
        link.symlink_to(path)
        for arguments in ((), (path, "--extra"), ("--unknown",), ("signal.wav",),
                          ("https://example.com/audio.wav",), ("file:///tmp/audio.wav",),
                          (self.directory,), (link,), (self.directory / "missing.wav",)):
            with self.subTest(arguments=arguments):
                self.rejected(*arguments)

    def test_oversize_file_is_rejected_without_loading_audio(self):
        path = self.directory / "oversize.wav"
        with path.open("wb") as stream:
            stream.write(b"RIFF")
            stream.truncate(12 * 1024 * 1024 + 1)
        self.rejected(path)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named pipes require POSIX")
    def test_named_pipe_is_rejected_without_waiting_for_a_writer(self):
        path = self.directory / "pipe.wav"
        os.mkfifo(path)
        process = subprocess.run([NODE, str(SCRIPT), str(path)],
                                 capture_output=True, text=True, timeout=3)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(json.loads(process.stdout)["ok"])

    def test_riff_headers_and_chunk_bounds_are_validated(self):
        valid = wav_bytes(tone(0.2))
        cases = {
            "not-riff": b"RIFX" + valid[4:],
            "not-wave": valid[:8] + b"AVI " + valid[12:],
            "short-header": b"RIFF\x00\x00",
            "truncated": valid[:-1],
            "trailing-bytes": valid + b"extra",
            "out-of-bounds-chunk": valid[:40] + struct.pack("<I", 0xFFFFFFFF) + valid[44:],
            "missing-fmt": riff_wave([riff_chunk(b"data", b"\0" * 4000)]),
            "missing-data": riff_wave([riff_chunk(b"fmt ", valid[20:36])]),
            "short-fmt": riff_wave([riff_chunk(b"fmt ", b"\0" * 12), riff_chunk(b"data", b"\0" * 4000)]),
            "empty-data": riff_wave([riff_chunk(b"fmt ", valid[20:36]), riff_chunk(b"data", b"")]),
            "partial-frame": riff_wave([riff_chunk(b"fmt ", valid[20:36]), riff_chunk(b"data", b"\0" * 4001)]),
            "duplicate-fmt": riff_wave([riff_chunk(b"fmt ", valid[20:36]),
                                        riff_chunk(b"fmt ", valid[20:36]), riff_chunk(b"data", valid[44:])]),
            "duplicate-data": riff_wave([riff_chunk(b"fmt ", valid[20:36]),
                                         riff_chunk(b"data", valid[44:]), riff_chunk(b"data", valid[44:])]),
        }
        for name, contents in cases.items():
            with self.subTest(case=name):
                self.rejected(self.write(f"{name}.wav", contents))

    def test_unsupported_or_inconsistent_audio_metadata_is_rejected(self):
        valid = wav_bytes(tone(0.2))
        patches = {
            "compressed": (20, "<H", 6), "no-channels": (22, "<H", 0),
            "surround": (22, "<H", 3), "low-rate": (24, "<I", 7999),
            "high-rate": (24, "<I", 48001), "bad-byte-rate": (28, "<I", 1),
            "bad-block-align": (32, "<H", 1), "unsupported-bits": (34, "<H", 12),
            "float16": (20, "<H", 3),
        }
        for name, (offset, fmt, value) in patches.items():
            with self.subTest(case=name):
                mutated = bytearray(valid)
                struct.pack_into(fmt, mutated, offset, value)
                self.rejected(self.write(f"{name}.wav", mutated))

    def test_float_samples_must_be_finite_and_normalized(self):
        for bits in (32, 64):
            for bad in (math.nan, math.inf, -math.inf, 1.01, -1.01):
                with self.subTest(bits=bits, value=bad):
                    samples = quiet(0.2)
                    samples[100] = bad
                    self.rejected(self.signal(samples, bits=bits, floating=True))

    def test_extensible_guid_and_valid_bits_are_checked(self):
        valid = wav_bytes(tone(0.2), extensible=True)
        for name, offset, replacement in (
            ("bad-subtype", 44, b"\x06"),
            ("bad-guid-suffix", 59, b"\x00"),
            ("bad-valid-bits", 38, b"\x18\x00"),
            ("short-extension", 36, b"\x14\x00"),
        ):
            with self.subTest(case=name):
                mutated = bytearray(valid)
                mutated[offset:offset + len(replacement)] = replacement
                self.rejected(self.write(f"{name}.wav", mutated))

    def test_chinese_usage_and_file_errors_are_readable_utf8(self):
        usage = self.rejected()
        self.assertIn("用法", usage["error"]["message"])
        missing = self.rejected(self.directory / "不存在的音频.wav")
        self.assertEqual(missing["error"]["code"], "FILE_NOT_FOUND")
        invalid = self.rejected(self.write("损坏音频.wav", b"not a WAV file"))
        self.assertEqual(invalid["error"]["code"], "INVALID_WAV")

    def test_chinese_results_preserve_machine_keys_and_enum_values(self):
        path = self.signal(quiet(0.2) + tone(0.6) + quiet(0.2), name="音高分析样本.wav")
        result = self.ok(path)
        for message in result["limitations"]:
            self.assert_chinese(message)
        self.assert_chinese(result["energy"]["measurement"])
        self.assert_chinese(result["tempo"]["definition"])
        self.assertEqual(result["audio"]["encoding"], "PCM")
        self.assertIn(result["pitch"]["ending"], ("rising", "falling", "steady", "insufficient_data"))
        self.assertIn(result["energy"]["ending"], ("increasing", "decreasing", "steady", "insufficient_data"))

    def test_packaged_instructions_and_metadata_are_utf8_chinese(self):
        manifest = json.loads((PAYLOAD / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "dsh-ears-prosody")
        self.assertEqual(manifest["version"], VERSION)
        for field in ("name", "description"):
            self.assert_chinese(manifest[field])
        for field in ("display_name", "display_description"):
            for text in manifest[field].values():
                self.assert_chinese(text)
        for relative in ("README.md", "skills/prosody-analysis/SKILL.md"):
            self.assert_chinese((PAYLOAD / relative).read_text(encoding="utf-8"))
        skill = (PAYLOAD / "skills/prosody-analysis/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("中文", skill)

    @unittest.skipUnless(BASELINE_ZIP, "Set PROSODY_BASELINE_ZIP for optional historical comparison")
    def test_measurements_match_preserved_1_0_0_package(self):
        self.assertEqual(hashlib.sha256(BASELINE_ZIP.read_bytes()).hexdigest(), BASELINE_SHA256,
                         "The independently preserved, previously tested baseline must not change.")
        baseline = self.directory / "baseline-1.0.0"
        baseline.mkdir()
        with zipfile.ZipFile(BASELINE_ZIP) as archive:
            for relative in ("scripts/analyze.mjs", "lib/wav.mjs", "lib/hearing.mjs"):
                target = baseline / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(f"dsh-ears-prosody/dsh-ears-prosody/{relative}"))

        def measurements(result):
            projection = json.loads(json.dumps(result))
            projection.pop("version")
            projection.pop("limitations")
            projection["energy"].pop("measurement")
            projection["tempo"].pop("definition")
            return projection

        rng = random.Random(20261022)
        cases = {
            "稳定音高": tone(0.6),
            "升调": quiet(0.2) + tone(1.2, 120, end_hz=260) + quiet(0.2),
            "停顿和能量变化": tone(0.4, 180, 0.08) + quiet(0.3) + tone(0.4, 260, 0.64),
            "静音": quiet(0.4),
            "随机噪声": [rng.uniform(-0.4, 0.4) for _ in range(SAMPLE_RATE)],
        }
        for name, samples in cases.items():
            with self.subTest(signal=name):
                path = self.signal(samples, name=f"{name}.wav")
                before = json.loads(subprocess.run(
                    [NODE, str(baseline / "scripts/analyze.mjs"), str(path)],
                    check=True, capture_output=True, text=True, encoding="utf-8", timeout=35,
                ).stdout)
                self.assertEqual(before["version"], "1.0.0")
                self.assertEqual(measurements(before), measurements(self.ok(path)))


@unittest.skipUnless(NODE, "Requires Node.js >=20 on PATH")
class ProsodyHostAdapterTests(FixtureTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from openjiuwen.core.common.logging.log_config import (
                configure_log_config, get_log_config_snapshot,
            )
            config = get_log_config_snapshot()
            config["log_path"] = str(Path(tempfile.gettempdir()) / "prosody-test-host-logs")
            configure_log_config(config)
            from openjiuwen.core.foundation.tool import Tool
        except ModuleNotFoundError as exc:
            if not exc.name.startswith("openjiuwen"):
                raise
            raise unittest.SkipTest("Requires the real WorkSwarm openJiuwen SDK") from exc
        spec = importlib.util.spec_from_file_location("prosody_adapter_under_test", PAYLOAD / "tools/prosody_tool.py")
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)
        cls.host_tool_type = Tool

    def test_adapter_executes_real_cli_and_returns_same_analysis(self):
        path = self.signal(quiet(0.2) + tone(0.6) + quiet(0.2), name="后端中文路径.wav")
        result = self.adapter.run_prosody({"path": str(path)})
        self.assertTrue(result["ok"], result)
        direct = json.loads(subprocess.run([NODE, str(SCRIPT), str(path)], check=True,
                                           capture_output=True, text=True, timeout=35).stdout)
        self.assertEqual(result, direct)

    def test_adapter_rejects_bad_inputs_without_launching_process(self):
        cases = (None, [], "path", 1, {}, {"path": None}, {"path": 1},
                 {"path": ""}, {"path": "relative.wav"}, {"path": "https://example.com/a.wav"},
                 {"path": "/tmp/a\0.wav"}, {"path": "/tmp/a.wav", "model": "paid"})
        with patch.object(self.adapter.subprocess, "run", side_effect=AssertionError("Invalid input launched Node")):
            for inputs in cases:
                with self.subTest(inputs=inputs):
                    result = self.adapter.run_prosody(inputs)
                    self.assertFalse(result["ok"], result)
                    self.assertEqual(result["error"]["code"], "invalid_input", result)
                    self.assert_chinese(result["error"]["message"])

    def test_adapter_reports_missing_node_without_fallback_download(self):
        path = self.signal(quiet(0.1))
        with patch.object(self.adapter.shutil, "which", return_value=None):
            result = self.adapter.run_prosody({"path": str(path)})
        self.assertFalse(result["ok"], result)
        self.assertIn("node", result["error"]["message"].lower())
        self.assert_chinese(result["error"]["message"])

    def test_adapter_timeout_is_a_structured_error(self):
        path = self.signal(quiet(0.1))
        with patch.object(self.adapter.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 30)):
            result = self.adapter.run_prosody({"path": str(path)})
        self.assertFalse(result["ok"], result)
        self.assert_chinese(result["error"]["message"])

    def test_host_tool_is_actual_sdk_tool_and_invokes_without_model(self):
        tool = self.adapter.ProsodyTool()
        self.assertIsInstance(tool, self.host_tool_type)
        self.assertEqual(tool.card.name, "analyze_wav_prosody")
        self.assert_chinese(tool.card.description)
        self.assert_chinese(tool.card.input_params["properties"]["path"]["description"])
        path = self.signal(tone(0.4))
        result = asyncio.run(tool.invoke({"path": str(path)}))
        self.assertTrue(result["ok"], result)
        self.assertAlmostEqual(result["pitch"]["meanHz"], 220, delta=10)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-demo-dir":
        print(json.dumps(make_demo_fixtures(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        unittest.main()
