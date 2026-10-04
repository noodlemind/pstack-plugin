# Verification and evidence boundaries

## Reproducible public checks

- `python3 -m unittest discover -s plugins/pstack/tests -v`: 119 adapter tests, including all budget choices, fresh users with no default, changes/persistence, native/cloud policy, task/decision/recovery, verification, cancellation and updater guards.
- `python3 -m unittest discover -s tools/tests -v`: staged-content privacy checks, secret masking, private artifacts, synthetic contacts and symlink rejection.
- `python3 tools/check_fresh_setup.py`: separate helper processes show no initial budget, rejected unconfigured planning, small then medium choices, preserved preference, actual executable verification, checkpoint recovery and no daemon/provider invocation.
- `python3 tools/check_upstream.py`: verifies all 187 archived source hashes and the unchanged Lauren Tan/Cursor license texts.
- Preserved upstream `bun test orch watch-pr` and `bun run typecheck`: orchestration/watch behavior and TypeScript checks against the pinned sources.
- `python3 tools/audit_repository.py`: checks exact staged blob content and artifact paths without echoing matched sensitive values. Run after staging intended files. It is not a guarantee against every possible secret or PII format.

The CI workflow is configured to run these checks on Linux and macOS with minimal repository permissions and pinned action revisions. The actual run status is the pass/fail record; committing this workflow alone does not verify either platform.

## What public tests do not prove

Provider calls are mocked or omitted in the public suite. A catalog fixture is labelled as a fixture; it does not establish account/model access. Private development exercised an installed native Codex workflow with real verification and recovery, plus optional CLI workflows, but personal transcripts and account-specific receipts are intentionally not imported into this repository.

Actual Codex Cloud installation/execution, native parallel coordination and scheduled continuation, live team automation delivery, authorized PR shipping, and future API providers remain incomplete or unverified as identified in ROADMAP.md and the coverage table. Native OpenAI-only panels do not meet a cross-provider independence requirement. No universal security or full upstream-equivalence claim follows from passing these tests.
