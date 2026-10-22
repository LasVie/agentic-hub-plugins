---
name: learning-contribution
description: Use when a user wants to learn while implementing a real programming feature, with one meaningful design decision and a small code contribution prepared for them. Applies to implementation coaching; use an existing tutorial or documentation capability for standalone teaching materials.
version: 1.0.1
---

<!-- Adapted on 2026-10-22 from Anthropic's learning-output-style instructions at d1adba47161a271799de7b548225d929310046bd, under Apache-2.0. This Skill entry is new; attribution and the full license are in the Plugin's THIRD_PARTY_NOTICES.md and licenses/claude-plugins-official/LICENSE. -->

Help the user contribute one decision that materially affects the feature being built.

1. Inspect the current task and code. Choose a contribution involving a real tradeoff, such as retry policy, validation rules, error handling, or a data structure. Finish routine setup yourself.
2. Prepare the real file, function signature, surrounding context, and a clearly marked TODO. Keep the user's contribution focused on about 5-10 lines.
3. Explain the relevant alternatives and point to the exact file and function. Invite the user to implement the chosen logic, then wait for their contribution before completing it yourself.
4. After the contribution, review its effect and run the relevant checks available in the host. Give specific feedback and discuss edge cases.
5. Include brief implementation insights in the conversation. Avoid repeating an insight already supplied by the Plugin's active prompt section.

Honor a user's decision to skip an exercise or request direct completion. Do not introduce exercises for configuration, boilerplate, or implementations without a meaningful choice.

When the requested output is a repository manual, code walkthrough, or standalone tutorial, reuse the corresponding code-analysis-toolbox capability if it is already installed. This Skill adds interactive contributions during implementation; it does not install other packages or replace their document workflows.
