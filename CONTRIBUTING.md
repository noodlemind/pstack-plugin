# Contributing

Keep the original pstack workflows and Lauren Tan (poteto)'s credit intact. Read NOTICE.md, SECURITY.md, AGENTS.md and the execution contract before changing behavior.

## Scope and changes

Use an issue to describe a bug, missing host capability or proposed change. Link the implementation PR to that issue. Each PR should explain the triggering problem, the new behavior, verification and remaining limits. Prefer small verifiable units. Keep provider choices and capability gaps explicit; multiple calls to one model do not prove model or provider diversity.

Do not edit `plugins/pstack/upstream/` directly. Fetch an exact upstream commit, plan/stage with the bundled updater, review conflicts and record the new pin and hashes. Changes to shared upstream procedures should preserve their attribution and, when suitable, be contributed upstream. Port-specific runtime changes belong in the adaptation.

## Development checks

Python 3.11+, Git, Bun and Node 20+ are needed for the full developer checks. Install pinned development dependencies from their lockfiles:

```sh
cd plugins/pstack/skills/poteto-mode/scripts
bun install --frozen-lockfile
cd ../../../../..
python3 -m unittest discover -s plugins/pstack/tests -v
python3 -m unittest discover -s tools/tests -v
python3 tools/check_fresh_setup.py
python3 tools/check_upstream.py
cd plugins/pstack/skills/poteto-mode/scripts
bun test orch watch-pr
bun run typecheck
```

Optional local browser helpers use `npm ci --prefix plugins/pstack/runtime --ignore-scripts` and need a compatible browser. Normal setup and native verification do not require Playwright or another provider CLI.

Before committing, stage only intended source, run `python3 tools/audit_repository.py`, and inspect the staged diff. The audit reads the Git index, including staged file content; ignored local artifacts are never evidence that the published tree is safe. CI reruns the audit, tests and original-source hash check. Use a GitHub noreply address for commits if you do not want your personal email published.

Never attach real user transcripts, login state, keys, environment dumps, screenshots containing personal data, or unredacted host paths to a PR. Reproduce with synthetic fixtures. If a failure needs private evidence, keep it outside this repository and share only a reviewed minimal report.

## License and review

Unless a contribution explicitly states otherwise and maintainers accept that exception, contributions to the adaptation are offered under this repository's MIT license. Only contribute material you have permission to redistribute. Preserve third-party copyrights and licenses; identify new dependencies, their licenses and why they are needed. There is no contributor agreement or requirement to publish a legal name or personal email.

A release requires a version change in both plugin manifests, relevant behavior tests, fresh-user setup, supported installation verification, privacy review and updated coverage. Never claim a cloud host or external provider works solely because a local fixture passed. Only mark a roadmap item complete after its acceptance criteria have actual evidence. Merge/deployment authority is separate from green CI.
