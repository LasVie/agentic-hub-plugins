# Deckaura Tarot 1.0.2

Offline reference and reflective draws from Deckaura's 78-card dataset. Includes a native Agentic Hub Plugin manifest, the `tarot-reading` Skill, and the `deckaura_tarot` Python tool. Candidate `CAND-CLD-140`; task `AH-20261022-deckaura-tarot`; port maintainer Cai Zhenze. Upstream author/rightsholder: Deckaura. This adaptation does not imply upstream endorsement.

## Requirements

- Node.js >=18 on the backend process PATH. No npm installation is required.
- An openJiuwen/WorkSwarm host exposing `openjiuwen.core.foundation.tool.Tool` and `ToolCard` for the Python adapter.
- The CLI works independently with Node.js. The tool makes no network or model calls. Conversational interpretation requires a separately configured host model; it is not needed for deterministic tool checks.

## Install

The repository's canonical Hub artifact is `deckaura-tarot-1.0.2.zip`, containing `deckaura-tarot/plugin.yaml` and `deckaura-tarot/deckaura-tarot/manifest.json`.

The tested WorkSwarm local importer supports only a root or single-directory manifest. For its Extensions plugin upload interface, use `deckaura-tarot-1.0.2-workswarm.zip`. It contains `deckaura-tarot/manifest.json` and the identical inner payload; it is a local-import companion, not a replacement for the canonical Hub artifact. See the repository `MANUAL_TESTING.md` for the isolated instance and recorded hashes.

After importing, confirm version 1.0.2, one Skill and one tool. Attach the Plugin to the intended Agent session to expose `deckaura_tarot`. If Node is missing, add it to the backend PATH and restart that backend.

## Tool examples

```json
{"action":"lookup","card":"The Star","orientation":"reversed"}
{"action":"draw","count":3,"reversals":false,"seed":"manual-demo"}
{"action":"spread","spread":"celtic-cross","seed":"manual-demo"}
{"action":"validate"}
```

Each call returns JSON with `ok`. Lookup returns one card and the exact source URL. Draws/spreads return unique cards, positions, orientations, meanings and a replayable seed. Validation returns 78 cards and the dataset SHA-256. Failed calls return `ok: false` and an actionable error.

Supported spreads: daily (1), three-card (3), decision (5), relationship (6), celtic-cross (10), yes-no (1). Counts must be integers from 1 to 78, reversal flags must be booleans, and orientations must be `upright` or `reversed`. A seed must be 1-256 characters without NUL or a leading `--`; do not use private questions as seeds. Unknown fields are rejected for the selected action. An omitted seed uses OS entropy, followed by a reproducible pseudorandom shuffle. This is not a cryptographic card-selection guarantee.

## Standalone CLI

From this package directory:

```sh
node skills/tarot-reading/scripts/tarot.mjs validate
node skills/tarot-reading/scripts/tarot.mjs lookup "The Star" --orientation reversed
node skills/tarot-reading/scripts/tarot.mjs spread three-card --seed manual-demo --reversals false
```

The upstream CLI is retained byte-for-byte. The native adapter adds strict parameter checks and a ten-second timeout. CLI users should use documented arguments: upstream accepts some invalid orientations/options silently and cannot correctly parse a seed beginning `--`.

## Scope and attribution

Use for reflection, journaling and creative exploration. Tarot does not establish facts, guarantee future events or replace professional advice. Dataset meanings and contextual interpretations must remain distinct.

Code, dataset and reference material originate from [Deckaura Tarot](https://github.com/gokimedia/claude-skill-tarot/tree/804c54558375416fd4fce605238927f39bbac1a2), upstream 1.0.0. Full upstream MIT text: [licenses/deckaura-tarot/LICENSE](licenses/deckaura-tarot/LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the bundled data-provenance reference. No upstream logos, fonts, card images or third-party services are bundled. No unified license for newly written repository material is declared here.
