# Existing-port comparison

This is a source review of five public repositories at the exact commits below, performed on 2026-10-03 America/New_York. Selected local tests supplement the review. These repositories were not installed as replacements, and their account-specific, cloud or live-provider behavior was not certified.

The original pstack manifest at [Cursor commit e43c7ee](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/.cursor-plugin/plugin.json) identifies Lauren Tan as author, MIT as its license and 0.15.9 as its version. The source contains `correct` and `benchmark-checklist`. This verifies repository contents, not the date or wording of a social-media announcement. No official endorsement of a port was established by this review; that does not prove no public endorsement exists anywhere.

## Observed implementation and boundaries

| Port and inspected commit | Useful implementation | Relevant limits or differences |
| --- | --- | --- |
| [michael-denyer/pstack-claude, 55430ba](https://github.com/michael-denyer/pstack-claude/tree/55430ba22ccc751ab608422761aff14b2f063e5d) | Codex marketplace, session hooks, per-role effort, native agent mapping, durable checkpoint locator, three-way upstream sync and a declared policy-fork registry | Pins pstack at `23e4138daa01c42d4969f7a5465f82704e64f798`, version 0.15.6. Excludes Benny, make-bot-ui and the control-cli/control-ui companion skills. Its Pi extension implements loop/wakeup support; that does not establish a Codex scheduler. |
| [ericlitman/open-pstack, 21d1546](https://github.com/ericlitman/open-pstack/tree/21d1546623634441290234639efa98d97c6ec835) | Shared Claude/Codex skills and a real external CLI runner with authentication preflight, requested/reported model checks, cancellation and receipts | Tracks pstack 0.15.5 at `12d587dfb20741cafc376c42c696c5f6e2a64487`. Codex does not load its Claude startup instruction. Some upstream behavior is deliberately excluded, including make-bot-ui and the upstream budget question. CLI support does not establish an API adapter. |
| [ScriptedAlchemy/pstack-codex, e68a46d](https://github.com/ScriptedAlchemy/pstack-codex/tree/e68a46d430d0427d9a7a7f0fb04f42bc63f62fe9) | Native marketplace, coverage inventory, upstream audit, persona profiles, scoped mode, Benny polling ledger and optional loopback bot UI bridge | Pins the same 0.15.5 commit as this adaptation. Its report separates local fixtures and recorded host tests from unverified cloud, scheduler delivery and live team integration. Standing instructions replace the upstream mode switch. |
| [Aqua-123/pstack-for-codex, 2bea6dc](https://github.com/Aqua-123/pstack-for-codex/tree/2bea6dca0da10e81d6579ec7e45d9ab1ece948c8) | Session-isolated sticky hooks, model/effort evidence checks, ownership-aware profile setup, Benny state reconciliation, source hashes and explicit refresh decisions | Lock identifies pstack 0.15.1 at `f8abeddd1862dc73704e3d719dd73df0d51b8c71`. Missing model evidence produces disclosed inheritance. Benny stays paused pending setup and canaries. No CLI/API-provider execution support was established in this review. |
| [sm0ol/pstack-codex, 280ad44](https://github.com/sm0ol/pstack-codex/tree/280ad44a5c19ffacdf8c5abf9a2022160360f3dd) | Smaller Codex adaptation, project model sheet, native coordination guidance and a reproducible port script | Pins `04166ac89136d36de2a87f24429e6cc307594953`. Benny is retained for provenance and is dormant. The model policy allows a reported substitute when unavailable. No test suite was found in the tracked tree. |

## Reproduced checks

Run these in a checkout of the corresponding pinned port. They use local fixtures and do not grant provider access.

| Port | Command | Observed result |
| --- | --- | --- |
| pstack-claude | `bun test tests/session-hook.test.mjs tests/resume.test.mjs tests/models.test.mjs tests/sync.test.mjs` | 188 passed on its CI-pinned Bun 1.3.14; hooks, model config, process recovery and sync fixtures |
| open-pstack | `bun test plugins/pstack/skills/poteto-mode/scripts/runner/commands.test.ts plugins/pstack/skills/poteto-mode/scripts/runner/parse-output.test.ts` | 11 passed on Bun 1.2.4; command construction and parsing, not authenticated execution |
| ScriptedAlchemy | `node --test plugins/pstack/automations/benny/scripts/ledger.test.mjs` | 8 passed on Node 26.9.0; separate-process persistence, locking and ambiguous-write recovery |
| Aqua | `node --test tests/poteto-mode-hooks.test.mjs tests/model-config.test.mjs tests/benny-state-machine.test.mjs` | 36 passed on Node 26.9.0; sticky lifecycle, model policy and automation recovery |
| sm0ol | Tracked source inventory and runtime-document review | No execution or installed-workflow result claimed |

The initial pstack-claude run used Bun 1.2.4 and produced 63 passes and one failure because that runtime lacks `Bun.YAML.parse`. That is a local dependency mismatch, not evidence of a plugin defect. The follow-up uses its CI-pinned runtime without changing the machine's global Bun installation.

## Decision

Existing ports invalidate a claim that Codex compatibility or external CLI execution alone is new. They also provide concrete work to reuse. They do not remove the value of a distribution that makes native execution, optional CLIs and future API providers consistent to configure and verify.

This repository will continue as an independent adaptation with the narrower [product direction](product-direction.md). Keep the native path useful without extra accounts, prove each optional execution path, preserve user choices and track upstream changes. Do not claim greater stability until comparable tests establish it. Do not claim full upstream behavior while the coverage table still has gaps.

No code from these five ports was imported during this review. If implementation is reused later, record the source commit and file provenance and preserve its notices and license. Changes to Lauren's workflows should be proposed to the original project when appropriate; provider integration and host compatibility belong in the adaptation.

## Source pointers

- pstack-claude: `tools/upstream.json`, `tools/sync.mjs`, `tools/forks.json`, `plugins/pstack/hooks/session-start.sh`, setup-pstack and `references/codex-tools.md`.
- open-pstack: `UPSTREAM.md`, `references/provider-dispatch.md`, `references/codex-tools.md`, `scripts/runner/commands.ts`, `scripts/runner/run.ts` and their tests under poteto-mode.
- ScriptedAlchemy: `UPSTREAM.json`, `PARITY.md`, `UPDATING.md`, `INTEGRATION-TESTS.md` and Benny's `scripts/ledger.mjs` and tests.
- Aqua: `upstream.lock.json`, `UPSTREAM.md`, `docs/codex-adaptation.md`, sticky hook scripts, setup agent manager and Benny reconciliation tests.
- sm0ol: `UPSTREAM_COMMIT`, `README.md`, `references/codex-runtime.md` and `scripts/port_upstream.py` under its plugin.
