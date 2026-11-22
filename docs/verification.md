# Verification and evidence boundaries

## Reproducible public checks

- `python3 -m unittest discover -s plugins/pstack/tests -v` covers budget choices, fresh users with no default, preference changes, native/cloud policy, task/decision/recovery, verification, cancellation and updater guards.
- `python3 -m unittest discover -s tools/tests -v` checks staged content for private artifacts, validates release integrity and replays a counterexample through the packaged statechart launcher.
- `python3 tools/check_fresh_setup.py`: separate helper processes show no initial budget, rejected unconfigured planning, small then medium choices, preserved preference, actual executable verification, checkpoint recovery and no daemon/provider invocation.
- `python3 tools/check_upstream.py` verifies the archived source hashes and the Lauren Tan and Cursor license texts.
- From `plugins/pstack/skills/poteto-mode/scripts`, `bun run test` and `bun run typecheck` exercise the PR watcher and type-check it against the pinned dependencies.
- From `plugins/pstack/skills/statechart/scripts`, `npm test` checks the compiler, recorded TLC runs and rendered Mermaid output. Setting `TLA2TOOLS` adds the live TLC cases. CI separately runs a passing and a failing model against the checksum-verified TLC 1.7.4 jar and compares their charts and reports with the committed fixtures.
- `python3 tools/audit_repository.py`: checks exact staged blob content and artifact paths without echoing matched sensitive values. Run after staging intended files. It is not a guarantee against every possible secret or PII format.

The CI workflow is configured to run these checks on Linux and macOS with minimal repository permissions and pinned action revisions. The actual run status is the pass/fail record; committing this workflow alone does not verify either platform.

## What public tests do not prove

Provider calls are mocked or omitted in the public suite. A catalog fixture is labelled as a fixture; it does not establish account/model access. Private development exercised an installed native Codex workflow with real verification and recovery, plus optional CLI workflows, but personal transcripts and account-specific receipts are intentionally not imported into this repository.

Actual Codex Cloud installation/execution, native parallel coordination and scheduled continuation, live team automation delivery, authorized PR shipping, and future API providers remain incomplete or unverified as identified in ROADMAP.md and the coverage table. Native OpenAI-only panels do not meet a cross-provider independence requirement. No universal security or full upstream-equivalence claim follows from passing these tests.
