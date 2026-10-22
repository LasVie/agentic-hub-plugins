# Third-party notices

## Anthropic Code Simplifier

Source: https://github.com/anthropics/claude-plugins-official

Pinned revision: `d1adba47161a271799de7b548225d929310046bd`.
Plugin: `plugins/code-simplifier`, upstream version `1.0.0`.
Original author: **Anthropic**, `support@anthropic.com`, as credited in the pinned
`.claude-plugin/plugin.json`. The upstream prompt has no separate copyright header;
no replacement ownership claim is added here.

License: **Apache-2.0**. Complete, unchanged texts are bundled in `LICENSE` and
`licenses/claude-plugins-official/LICENSE`.
Covered adaptation: upstream `plugins/code-simplifier/agents/code-simplifier.md`
is adapted in `skills/code-simplifier/SKILL.md`. The license is copied unchanged.
No other upstream code, icons, fonts, data, services or dependencies are bundled.

No separate upstream NOTICE exists at the root, `plugins/`, or within this plugin
at the pinned revision. This file is an attribution inventory, not a fabricated
upstream NOTICE, and does not change license terms.

## Modifications

The supplied 1.0.0 package records its 2026-10-21 adaptation: agent prompt converted
to a native skill; model override and automatic invocation removed; conventions
generalized; scope/verification limits, native manifest and bilingual metadata
added. Its skill-level adaptation notice is retained.

Version **1.0.1**, repackaged **2026-10-22** at **Cai Zhenze**'s request:

- Preserved `skills/code-simplifier/SKILL.md` byte for byte from the supplied ZIP.
- Changed only the package version in `manifest.json`.
- Updated README with archive names, layouts and a prominent repack notice.
- Added this inventory and the conventional full-license path.
- Added the marketplace wrapper outside the native payload; the native test ZIP
  contains exactly the same payload files.

No Anthropic endorsement or general trademark rights are claimed. Packaging-member
metadata does not replace upstream attribution or relicense unrelated materials.
