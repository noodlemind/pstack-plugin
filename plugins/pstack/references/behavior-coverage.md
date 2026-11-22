# pstack behavior coverage — native execution design

Current package: **0.15.46-openai.9**. Upstream pin: `7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9` (pstack 0.15.46). This independent port executes inside the current coding host. All original source files, both MIT licenses and attribution remain preserved. Private development receipts are not published. Current checks are reproducible from this source tree; live-host coverage is identified separately.

| Upstream capability | Current implementation | Evidence and limits |
| --- | --- | --- |
| Skills, playbooks, principles, four agents | 82 installed skills, 22 playbooks and four agent-role skills; original engineering steps retained with a host execution contract | Native plugin discovery; original archive hash verification; installed skill directory and upstream inventory |
| Correct | Scoped history, mistake classes, architecture/types/lint/tests before docs, rule-to-enforcement table | Release updater corrections and negative regression fixtures; no claim of exhaustive repository history mining |
| Benchmark checklist and Explain the Number | Seven evidence questions, interleaved repeats, error/work counts, platform-specific profiler guidance | Invalid skipped-work benchmark inspected in an installed workflow; broader model judgment remains unverified |
| Sticky poteto-mode and routing | Scoped persistent mode, playbook selection, trusted context hooks; explicit context reads when hooks unavailable | Existing mode/routing tests plus fresh installed native workflow. Cloud automatic hooks are not assumed |
| Setup and coding harness detection | Passive executable inventory; native execution default; unsupported adapters disabled; no credential reads or program execution during scan | New harness tests and real local setup receipt. candidate presence and authentication are reported separately; installed tools differ by host |
| Model discovery | Current host OpenAI catalog for native work; only explicitly selected local CLI catalogs may be queried | Host catalog integration was exercised during private development; this public suite uses labelled fixtures. Availability must be checked in each actual host |
| Per-role models and reasoning | Nine active native roles, preserved legacy selections, explicit user choices, host catalog validation, supported-effort clamping, persistent budget; old CLI choices retained inactive | Native role/budget persistence and retired-model rejection tests; fresh users must choose a budget; existing explicit choices retained |
| Local optional model harnesses | Explicit same-machine opt-in, supported adapter and verified model required | Guards tested; prior real Codex/Claude/Grok adapter receipts remain historical. Adapters are currently disabled |
| Cloud execution | Native OpenAI only; rejects local CLI activation and copied local profiles; no connection to another computer | Local policy tests passed. Actual Codex Cloud account/task installation and execution remain unverified |
| Future API providers | Separate explicit provider setup with secrets belonging to the executing environment; cloud calls providers directly | Design preserved; disabled and not configured in this release |
| Parallel agents and reuse | Current host's native agent tools; fresh agents for new work and retries, reuse only for costly-to-move local state; isolated writer ownership; sequential operation when delegation unavailable/forbidden | Native tracking/recovery tests. Fresh installed workflow is sequential; prior parallel CLI receipts do not establish native cloud parallelism |
| Arena, swarm, adversarial panels | Native plans with actual model choices, isolated outputs, rubric/cross-judge/synthesis/verification; reduced diversity disclosed | Distinct-model and repeated-model plan tests. OpenAI-only panels never claim cross-provider equivalence |
| Tasks and decisions | Native plan plus durable scoped tasks, dependency checks, skipped-step reasons and append-only decisions | Runtime tests and fresh installed native workflow |
| Verification | Native shell/browser tools; helper captures executable proof, exact Git head, output and artifact changes | Runtime positive/negative verification tests and real installed PASS receipt |
| Session recovery | Checkpoints, tasks, decisions and actual native IDs/results; scope checks and fresh verification after restart | Fresh-process recovery and interrupted native-record tests. Ephemeral cloud state must be exported to host durable storage |
| Background work and /loop | Prefer host background/continuation/scheduler facilities; explicit predicates, budgets and cancellation. Optional local CLI loop retained behind opt-in | Existing bounded loop/cancel/recovery tests; native mode blocks legacy CLI loops. No promise of work after cloud container termination |
| PR monitoring and review remediation | Current host GitHub access or authenticated gh; exact head, review threads and CI; preserved watch-pr | Prior real read/watch evidence and unchanged guards. Live remediation/push/reply test still needs an authorized target |
| Authorized shipping | Native independent reviewer and real exact-head receipts; explicit merge authorization. Strict optional CLI gate retained | Existing guard tests; no real remote merge test. OpenAI-only review's provider-independence limit stays explicit |
| deslop, control-cli, control-ui | Preserved team-kit workflows; prefer current host shell/browser; optional local evidence helpers | Existing actual browser/PTY evidence and current runtime tests. A cloud host cannot access desktop-only surfaces |
| Benny triage/reproduce/fix automations | Native connectors/scheduler, project identities, two repros and bounded draft fix; no public receiver required | Existing gate/repro tests; real project/channel/tracker schedules remain dormant until configured |
| Weekly review, recall, reflect, workflow extraction | Workspace-scoped checkpoint/history and native authorized history tools | Adapted procedures retained; no scan of unrelated personal histories |
| Personal installation | Supported local marketplace update; no MCP server/app mapping in installed plugin | 82 skills; no MCP/app registration; supported personal installer preserves unrelated configuration |
| Remote computer access | No remote bridge or endpoint in this source distribution | Manifest/source checks; earlier private development services are not part of this repository |
| Future upstream updates | Pinned originals, three-way plan/stage, semantic conflict review and preserved adapter policy | Version and archive checks, three-way staging regressions, executable launcher checks, and installed setup/recovery checks; see docs/upstream-0.15.46.md |

The native host owns permissions and execution. Helper directory scoping is not an OS sandbox. The package starts no network listener during normal setup/state/verification. Optional loopback UI/control helpers are local development tools and must not be published or tunneled.

The adapter tests cover the retained runtime and the new environment policy; the removed remote-server tests are no longer counted. Read the repository docs/verification.md for actual installed-run results and remaining live-host gaps.

## Skill inventory

Each directory in [skills](../skills/) contains a discoverable workflow or role. The [upstream inventory](upstream-inventory.json) records the original paths and hashes. Eight skills arrived in this update.

| Skills | Use |
| --- | --- |
| `statechart` | Run TLC on a TLA+ model and render reachable states and property failures. |
| `create-formal-verification-skill`, `maintain-formal-verification-skill` | Build and maintain a project-specific model or proof and relate its properties to running code. |
| `ketchup`, `ketchup-video` | Brief the operator and optionally prepare a short subtitled video when the host supports the required media tools. |
| `poteto-help`, `in-your-own-words`, `sharpen` | Find the right workflow, restate the goal, or refine the task before execution. |

## Playbooks, agents, configuration and dependencies

The package contains 22 playbooks. The table records their scope and remaining live-workflow limits.

| Playbook | Native implementation and verification limit |
| --- | --- |
| authoring-a-skill | Host skill authoring plus actual validation; no new project skill tested here |
| autonomous-run | Host continuation, explicit predicate and stop/cancel limits; native idle wake needs a scheduler |
| autopilot-full | Original complete sequence with native checkpoints and verification; full application run untested |
| autopilot-stack | Inherits autopilot-full, stacks only dependent PRs, and stops for operator handoff at verified green heads |
| babysit | Native GitHub/gh checks and review remediation; historical read/watch evidence, no authorized mutation target |
| bug-fix | Reproduce, native fix, actual proof; prior optional CLI repair receipt is historical |
| eval | Blinded rubric and evidence preserved; project-specific evaluation untested |
| feature | Native exploration, architecture, implementation and verification; application-specific run untested |
| hillclimb | Explicit metric, iteration budget and real measurement; metric target not supplied |
| investigation | Fresh installed native run completed with real verification and recorded skipped steps |
| multi-phase-plan | Durable dependency units and decisions; project-specific plan not supplied |
| opening-a-pr | Current host Git/PR integration and attachment; actual PR creation not tested |
| pause-safely | Host cancellation plus scoped checkpoint; runtime cancellation guards and recovery tests |
| perf-issue | Actual measurement and profiling required; no performance improvement claimed |
| prototype | Host artifacts and browser with original steps; design target not supplied |
| refactoring | Owned edits and behavior proof; shared verification tested, no application refactor claimed |
| runtime-forensics | Native tools or optional local controls; historical browser/PTY evidence |
| session-pickup | Native IDs, checkpoints and re-verification; fresh-process recovery passed |
| shipping | Exact-head independent review, real receipts and explicit authority; actual merge untested |
| trace-forensics | Native trace/profile inspection or optional controls; historical real captures |
| visual-parity | Native fresh screenshots and actions; target design comparison untested |
| worktree-cleanup | Native recoverable archive or ownership/dirty checks; existing guard and local cleanup evidence |

Four upstream agents map to the installed skills `agent-poteto-agent`, `agent-comment-sicko`, `agent-ci-watcher`, and `agent-thermo-nuclear-code-quality-review`. Dispatch/reuse follows the current host's native agent tools and repository restrictions. Their original role prompts are retained; this release does not claim an individual live test of each prompt. The two team-kit rules, `no-inline-imports` and `typescript-exhaustive-switch`, remain in the rule skill, context hooks and worker contract.

Benny retains `setup-benny`, `triage-issue-reports`, `reproduce-and-fix-issues`, both scheduled prompt templates, owner configuration, feature map and routing/control references. Native coordinator execution keeps the original gates; the optional CLI-specific helper gates cannot be satisfied with invented native job records. Live automation activation remains incomplete. See the bundled Benny setup guide.

| Mechanism or external dependency | Current handling / evidence |
| --- | --- |
| Cursor manifest/skills/agents/rules | Root manifest plus native Codex manifest, 82 packaged skills, optional trusted lifecycle bridge; no MCP/app registration |
| pstack-models.mdc, user model prompts, speed/reasoning suffixes | Persistent SQLite configuration with explicit role/budget choices and exact host identifiers; no guessed Cursor model IDs |
| Task/TodoWrite/background/update_state | Native agent/plan/continuation tools plus durable tasks and checkpoints; actual host restrictions apply |
| create-skill/context-loader/history | Native skill authoring and scoped task history; no unrelated personal transcript scan |
| Python and SQLite | Python 3.11+ and standard library for helpers; installed tests ran under Python 3.12; interpreter required in the executing environment |
| Bun and Commander | The upstream PR watcher uses Bun and Commander 14. The upstream Bun orchestration command was retired |
| Node and Playwright | Optional browser helper bundles Playwright 1.63.0; its package requires Node 20+; browser availability remains host-specific |
| Chrome/Electron/CDP | Prefer native browser tools; optional local captures have historical evidence; no live Electron target provided |
| tmux/terminal control | Native terminal tools or local PTY helper; tmux is not required |
| Codex/OpenAI models | Native model metadata is host-scoped; prior local inference proof is not a capability promise for new users |
| Claude Code, Grok Build, Gemini CLI | Detected supported adapters, disabled by default; previous Claude/Grok receipts historical; prior Gemini probe failed UNSUPPORTED_CLIENT and needs a fresh authorized setup test |
| Cursor Agent, OpenCode, Aider, Copilot CLI | Passive candidate detection only; unsupported adapters stay disabled and are not claimed equivalent |
| External model APIs | Disabled, including direct prototype calls and credential inspection; separate future environment-local setup |
| Git/gh/GitHub CI/PR/stack frontier | Native integrations or same-environment CLI; historical authenticated reads/watch; mutations require a target and authority |
| Graphite and optional Origin shipping | Explicit frozen GitHub frontier is the default adaptation; no Graphite/Origin account access claimed |
| jq/curl and upstream shell helpers | Retained where referenced; check availability before each actual environment's workflow |
| Slack/tracker/Linear | Existing native connectors and coordinator-only writes; project/channel/identity/access and posting authority remain required; no live scheduled delivery proof |
| Notion/Sentry/Datadog/Databricks and other investigation sources | Discover actual authorized host integrations; unavailable sources remain evidence gaps |
| Tailscale/Grok Bot/webhook/SendToUser | Native host continuation/notifications; optional loopback-only local UI; no forwarding or remote computer access |
| Cursor /loop | Native continuation/scheduler when available; optional same-machine CLI loop is disabled by default; no cloud wakeup claim |
| Marketplace, hooks and state | Supported personal install, preserved other entries, state outside cache; hooks require host trust, explicit context reads are the fallback |
| Former MCP SDK/Uvicorn/OAuth/Railway dependencies | Removed from active runtime and private installation; attribution and historical receipts retained only |

Every original source/configuration/template/asset is listed with its path and SHA-256 in `upstream-inventory.json`: 582 original files remain byte-identical. Git records adapter changes separately; tools/check_upstream.py verifies originals. Inventory and preserved instructions alone are not behavioral proof.
