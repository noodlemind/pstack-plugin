# pstack 0.15.46 update for Codex

Adapter `0.15.46-openai.9` updates the previous release, `0.15.9-openai.8`. On November 22, 2026, the official repository’s main branch pointed to `7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9`. Its latest pstack change was `0b46ec39`, which added native Windows support to the statechart runner. [Official sources](https://github.com/cursor/plugins/tree/7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9/pstack) · [Tracking issue](https://github.com/noodlemind/pstack-plugin/issues/17)

## What changed

The three-way update added 422 upstream files, changed 91 and removed 30. Of the 543 changes, 410 belong to the new statechart skill, including its compiler, model corpus and expected output. The companion cursor-team-kit tree and both MIT licenses were unchanged. The archive holds 582 files and the installed package exposes 82 skills and 22 playbooks. [Upstream comparison](https://github.com/cursor/plugins/compare/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a...7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9)

| Area | Effect on the Codex port |
| --- | --- |
| Formal verification | `statechart` checks TLA+ models with TLC and writes a Mermaid chart and diagnostic report. Two companion skills create and maintain project verification procedures. The updater preserves executable bits. The Codex launcher resolves its physical directory so a relative link inside a symlinked directory finds the TypeScript entry point on macOS and Linux. |
| Orchestration | The port routes program-scale work and saved orchestrate sessions to the installed `figure-it-out` skill. Explicit planning requests keep the multi-phase plan procedure. An operator can read or refresh an existing frontier store. New work uses tasks, decisions, checkpoints and native workers. |
| Plans and PRs | Task extraction handles bullet lists and procedural paragraphs. The PR watcher remains available. The retired Bun orchestrator and plan checker were removed. Autopilot-stack hands verified green PRs to the operator. |
| Setup and briefings | Setup uses the current host’s model catalog and the user’s chosen reasoning budget. New skills provide a help index, restate or sharpen a request, and deliver written or subtitled video updates. |
| Upgrades | Published retirement records identify old files by digest. A clean upgrade directly from 0.15.5-openai.7 was also exercised. Each released bundle keeps its source attribution, executable modes and review record. |

Five files needed a manual decision. The plugin README retains the Codex installation instructions. Setup uses the current host's configuration and offers optional formal verification. The bot UI stays loopback-only. The benchmark checklist retains platform-specific probes. Benny uses the adapted project settings and coordinator authorization. The [machine-readable review](../plugins/pstack/UPDATE-REVIEW.json) records the five paths and groups each changed upstream file by subsystem.

## Verification

| Linux check | Result |
| --- | --- |
| Adapter runtime and installer | 136 tests passed. |
| Release integrity and publication checks | 11 tests passed. Both archived Git tree IDs match the upstream pin, including file modes. |
| PR watcher | 54 tests passed and strict TypeScript checking passed. |
| Statechart compiler | With TLC 1.7.4, all 407 tests passed with zero skips. The ordinary developer run also passed, with 70 live-model cases gated on `TLA2TOOLS`. |

An isolated Codex CLI installation exercised the candidate marketplace entry, preserved an unrelated entry, and passed the first-use, verification and recovery workflow. An upgrade from 0.15.9-openai.8 removed 60 obsolete archive and adapted paths and preserved the saved reasoning budget and a user-added file. Separate upgrades with edits to a retained or retired file stopped before replacing the prior installation. A repeat install completed without duplicating marketplace entries or compatibility hooks. Injecting a plugin-add failure after a real Codex marketplace registration restored the prior local installation. A retry completed successfully. On Linux, live TLC runs on a four-state counter and on a failing model produced the expected charts and reports. See the [verification commands](verification.md) and the machine-readable review for results and evidence limits.

The review did not exercise native Windows, a Codex Cloud scheduler, cross-provider panels, or live delivery by team automations.
