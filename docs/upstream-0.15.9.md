# Upstream 0.15.9 update

On 2026-10-04, the latest official `cursor/plugins` main resolved to `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`, with pstack 0.15.9. This update advances the adaptation from 0.15.5-openai.7 to **0.15.9-openai.8**. The upstream commit was published October 3 in America/New_York. [Original source](https://github.com/cursor/plugins/tree/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack). [Tracking issue](https://github.com/noodlemind/pstack-plugin/issues/4).

## Scope and design

The reviewed three-way updater imported all 21 changed files and three new skills. The resulting bundle has 74 skills, 24 principles, 23 playbooks and four agent roles. All 190 original files and both licenses are byte-preserved. No cursor-team-kit file or external dependency changed upstream.

A clean replacement would lose the native execution policy and explicit setup. The selected approach merges the archived upstream delta into the adaptation, reviews adapter-owned files, and keeps private configuration outside the package. Git retains the previous archive; private staging also preserves its snapshot. There were no upstream deletions. The only merge blocker was the adapter README, resolved by retaining our setup and limitations while documenting the new release.

The updater now derives all package versions from one adapter version and preserves the adapter homepage. It excludes dependency installations and previous staging metadata. It regenerates the inventory descriptions, reference lists and playbook steps from the new originals, preserving the full inventory rather than reducing it to hashes. The release checker rejects a mismatched manifest, stale runtime package version or missing adapted skill even when the archive itself is intact. These corrections apply **Model the Domain** by assigning release identity one owner, and **Prove It Works** through negative tests and an installed candidate.

The throughput checkpoint had one gate, the exact-pin delta review. Source import, compatibility edits and evidence share the same package and stayed with one writer. Test suites ran independently after the edits. Parallel agent review was skipped under the repository's sequential-work instruction; no diverse panel is claimed.

## Every changed upstream file

Paths below are relative to the official cursor/plugins repository.

| File | Resolution |
| --- | --- |
| `pstack/.cursor-plugin/plugin.json` | Archive the original manifest; advance both adapter manifests and runtime packages to 0.15.9-openai.8. |
| `pstack/README.md` | Resolve adapter-owned README manually; expose new skills, current pin, original credit and existing capability limits. |
| `pstack/agents/poteto-agent.md` | Fresh agents for new tasks; resume only for the stateful exceptions in poteto-mode. |
| `pstack/docs/guide/08-principles.md` | 24 principles and Explain the Number link retained. |
| `pstack/docs/guide/README.md` | Guide index now names 24 principles. |
| `pstack/skills/architect/SKILL.md` | Design review assumes agents see partial context; favor changes that stay correct across the repository. |
| `pstack/skills/architect/references/design-red-flags.md` | Add split ownership, duplicate paths, importable internals and hand-synced lists. |
| `pstack/skills/benchmark-checklist/SKILL.md` | Retain all seven questions; add Linux/macOS tool mapping and preserve unrelated user processes. |
| `pstack/skills/correct/SKILL.md` | Retain mistake classes, architecture/types/lint/tests order, historical negative proof and enforcement table; constrain history to the current project. |
| `pstack/skills/poteto-mode/SKILL.md` | Retain plain-language responses, benchmark trigger, new principle and strict fresh-agent policy; native host contract remains authoritative. |
| `pstack/skills/poteto-mode/playbooks/autopilot-full.md` | Fresh owners, unit pushes, hourly audit, live liveness proof and conditional merge-time rebase; no implicit goal or merge authorization. |
| `pstack/skills/poteto-mode/playbooks/autopilot-stack.md` | Hourly audit, unit pushes, removal of implicit goal and immediate zero-write hold retained. |
| `pstack/skills/poteto-mode/playbooks/hillclimb.md` | Vet harness before freezing; print errors/work counts; borrow performance mantra order without early-stop rule. |
| `pstack/skills/poteto-mode/playbooks/multi-phase-plan.md` | Hourly loop and built-in PR tool preference; native hourly scheduling mapping remains conditional on host availability. |
| `pstack/skills/poteto-mode/playbooks/opening-a-pr.md` | Retain new Why/What changed/Scope structure and built-in PR create/edit preference. |
| `pstack/skills/poteto-mode/playbooks/perf-issue.md` | Vet every measurement; use seven ordered performance mantras and stop when an earlier one meets the target. |
| `pstack/skills/poteto-mode/scripts/check-plan.mjs` | Exact upstream checker now requires /loop 1h and no longer requires /goal or a 30-minute marker; positive and negative fixture tests pass. |
| `pstack/skills/principle-explain-the-number/SKILL.md` | Retain measured limiter, alternative explanations, counts/spread and benchmark link. |
| `pstack/skills/swarm/SKILL.md` | Respawn a worker after an invalid evidence report rather than reusing it. |
| `pstack/skills/technical-writing/SKILL.md` | Retain writing rules and remove obsolete fetched-date source annotations per upstream. |
| `pstack/skills/typescript-best-practices/references/patterns.md` | Retain schema-owned parsing and typed validator example; no new Zod runtime dependency is introduced. |

## Verification

- Installed the separately named `pstack-release-review` candidate through Codex's supported marketplace commands. Ran 122 adapter tests against its installed cache. Provider calls remain fixtures or absent.
- Ran 52 upstream orchestration/watch tests and the TypeScript check. Ran nine public release/privacy tests, including acceptance of the new hourly plan and rejection of the old cadence.
- Verified all 190 original hashes, both original license texts, matching package versions and 74 mapped skills against the installed candidate.
- Ran first-use in separate installed helper processes. No initial budget was selected. Unconfigured planning was rejected. Small and medium choices persisted. A real command produced a verification receipt, then a new process recovered its checkpoint.
- Applied the installed `/correct` procedure to updater regressions. Both new updater checks fail against the previous committed updater and pass against the correction. The enforcement table lives in AGENTS.md.
- Applied the installed benchmark checklist to a deliberately invalid generator benchmark. Five interleaved runs per side showed the supposed faster side did zero work, while the consumed side processed 100,000 rows and produced the expected checksum. A separate profile identified the rows function as the hot spot. The comparison was rejected; no performance improvement is claimed.
- Activated the installed perf playbook, retained its six steps including benchmark review, and recovered its mode/tasks/checkpoint in fresh processes. Native mode continued to reject the optional CLI loop path.

The public `UPDATE-REVIEW.json` contains sanitized review details. Private raw receipts, local paths, model preferences and account state are excluded. `tools/check_upstream.py --plugin-root <installed-root>` and `tools/check_fresh_setup.py --plugin-root <installed-root>` reproduce the installation checks.

## Remaining limits

This update imports the latest upstream behavior; it does not resolve the pre-existing live-host gaps. Real native parallel coordination, scheduled hourly wake/cancel, Codex Cloud execution, cross-provider panels, team automations and authorized remote shipping still need their separate verification. APIs remain disabled. No new goal, schedule, provider selection, network listener or laptop connection was created. See the coverage table and remaining roadmap issues.
