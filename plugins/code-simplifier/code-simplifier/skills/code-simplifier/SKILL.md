---
name: code-simplifier
description: Simplify and refine code for readability, consistency, and maintainability while preserving functionality. Use when asked to simplify code or review recent edits for clarity; focus on code modified in the current session unless a broader scope is explicitly requested.
---

# Code Simplifier

Adapted from Anthropic's Code Simplifier, licensed under Apache-2.0.
Modified for JiuwenSwarm on 2026-10-21: converted the agent definition into a
skill, removed model selection and automatic invocation instructions, and made
project conventions language-neutral. Source revision and changes: [README](../../README.md);
license: [LICENSE](../../LICENSE).

Improve code clarity and maintainability while preserving exact functionality.
Prefer readable, explicit code over overly compact solutions.

## Preserve behavior and scope

- Preserve features, outputs, public interfaces, side effects, and error behavior.
  Do not include bug fixes or other intentional behavior changes in a simplification.
- Normally work only on code modified or touched in the current session. Use
  available diffs and session context to identify it; examine surrounding code
  for understanding without expanding the edit scope.
- Honor an explicitly requested file, function, or broader scope. If the scope
  cannot be established, ask for it instead of refactoring the whole project.
- Preserve unrelated user changes. Do not reset, discard, or rewrite their work.

## Follow the target project

Read the applicable repository and directory instructions before editing, such
as AGENTS.md, CLAUDE.md where applicable, contribution guides, and relevant
configuration. Follow the target project's language idioms, naming, typing,
imports, error handling, formatting, and testing conventions. Use surrounding
code to resolve gaps.

Do not impose JavaScript, React, Python, or JiuwenSwarm-specific conventions on
other projects. Respect restrictions on commands, formatters, static analysis,
network access, and file changes.

## Simplify carefully

Look for unnecessary nesting, redundant logic or abstractions, unclear names,
and related logic that can be expressed more directly. Remove comments that
only repeat obvious code while preserving rationale and useful documentation.

Prefer clear control flow over dense expressions or nested conditionals when
that fits the language and project. Keep useful abstractions and separation of
concerns. Avoid clever rewrites, unrelated cleanup, dependency changes, and
optimizing for fewer lines at the expense of readability.

## Workflow

1. Identify the authorized scope and applicable project instructions.
2. Read the changed code and relevant callers and tests to understand behavior.
3. Make small, local simplifications whose behavior you can justify. Leave
   uncertain transformations unchanged and explain any meaningful limitation.
4. Review the resulting diff for accidental behavior changes and unrelated edits.
   Run relevant focused tests or checks that the project permits. If checks
   cannot run, state why; passing static checks alone does not prove unchanged
   runtime behavior.
5. Summarize significant changes, the scope, checks actually run and their
   results, and remaining verification gaps. If no useful simplification is
   warranted, say so without making cosmetic edits.

Use the host agent's existing reading, editing, and test tools within its
permissions. This skill does not create another agent, select a model, or
schedule itself after edits.
