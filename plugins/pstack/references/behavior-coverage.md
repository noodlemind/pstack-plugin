# pstack behavior coverage — native execution design

Current package: **0.15.5-openai.7**. Upstream pin: `7022c81efb48d8b5eb15498ce6043a3bd74b694c` (pstack 0.15.5). This independent port executes inside the current coding host. All original source files, both MIT licenses and attribution remain preserved. Private development receipts are not published. Current checks are reproducible from this source tree; live-host coverage is identified separately.

| Upstream capability | Current implementation | Evidence and limits |
| --- | --- | --- |
| Skills, playbooks, principles, four agents | 71 installed skills, 23 playbooks and four agent-role skills; original engineering steps retained with a host execution contract | Native plugin discovery; original archive hash verification; complete per-skill inventory below |
| Sticky poteto-mode and routing | Scoped persistent mode, playbook selection, trusted context hooks; explicit context reads when hooks unavailable | Existing mode/routing tests plus fresh installed native workflow. Cloud automatic hooks are not assumed |
| Setup and coding harness detection | Passive executable inventory; native execution default; unsupported adapters disabled; no credential reads or program execution during scan | New harness tests and real local setup receipt. candidate presence and authentication are reported separately; installed tools differ by host |
| Model discovery | Current host OpenAI catalog for native work; only explicitly selected local CLI catalogs may be queried | Host catalog integration was exercised during private development; this public suite uses labelled fixtures. Availability must be checked in each actual host |
| Per-role models and reasoning | Saved native roles, explicit user choices, host catalog validation, supported-effort clamping, persistent budget; old CLI choices retained inactive | Native role/budget persistence and retired-model rejection tests; fresh users must choose a budget; existing explicit choices retained |
| Local optional model harnesses | Explicit same-machine opt-in, supported adapter and verified model required | Guards tested; prior real Codex/Claude/Grok adapter receipts remain historical. Adapters are currently disabled |
| Cloud execution | Native OpenAI only; rejects local CLI activation and copied local profiles; no connection to another computer | Local policy tests passed. Actual Codex Cloud account/task installation and execution remain unverified |
| Future API providers | Separate explicit provider setup with secrets belonging to the executing environment; cloud calls providers directly | Design preserved; disabled and not configured in this release |
| Parallel agents and reuse | Current host's native agent tools; retain actual IDs; isolated writer ownership; sequential operation when delegation unavailable/forbidden | Native tracking/recovery tests. Fresh installed workflow is sequential; prior parallel CLI receipts do not establish native cloud parallelism |
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
| Personal installation | Supported local marketplace update; no MCP server/app mapping in installed plugin | 71 skills; no MCP/app registration; supported personal installer preserves unrelated configuration |
| Remote computer access | No remote bridge or endpoint in this source distribution | Manifest/source checks; earlier private development services are not part of this repository |
| Future upstream updates | Pinned originals, three-way plan/stage, semantic conflict review and preserved adapter policy | Existing update tests and staged update preservation check; no unreviewed newer pin installed |

The native host owns permissions and execution. Helper directory scoping is not an OS sandbox. The package starts no network listener during normal setup/state/verification. Optional loopback UI/control helpers are local development tools and must not be published or tunneled.

The 119 adapter tests cover the retained runtime and the new environment policy; the removed remote-server tests are no longer counted. Read the repository docs/verification.md for actual installed-run results and remaining live-host gaps.

## Per-skill inventory

Every skill below uses `references/runtime-contract.md` for native dispatch and reduced-capability reporting. Original procedures and supporting files are preserved under `upstream/`. Verification is shared by its relevant capability row above; inventory presence alone is not a workflow pass.

| Installed skill | Procedure |
| --- | --- |
| agent-ci-watcher | Watch PR CI for the current branch and report pass/fail with relevant failure links. Use when waiting for CI results or CI has failed. Use proactively to monitor branch CI. |
| agent-comment-sicko | A deranged comment-hater that savors deletion and condemns workaround code. |
| agent-poteto-agent | Routing target for `/poteto-mode` and any request for poteto's style. Resume an existing `poteto-agent` for the conversation rather than spawning a sibling. Reads the `poteto-mode` skill's `SKILL.md` in full be |
| agent-thermo-nuclear-code-quality-review | Thermo-nuclear code quality audit (maintainability, structure, 1k-line rule, spaghetti, code-judo). Invoked via Task after a parent gathers diff and file contents. Loads the rubric from the `thermo-nuclear-code |
| architect | Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code wo |
| arena | Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact w |
| automate-me | Use for \"automate me\", \"create/update/refresh my -mode skill\", \"turn/capture my preferences or working style into a skill\", or wanting agents to follow how the user works. Drafts or revises a personal -mo |
| blast-radius | Find what a change could break somewhere else before it ships, beyond the diff, and prove the one fact it's safe because of by running real code instead of writing it up. Use for 'blast radius of X', 'what coul |
| bro | Restate the last message in plain human language, with no jargon. |
| check-compiler-errors | Run compile and type-check commands and report failures |
| control-cli | Build or adapt a local harness to drive, inspect, and profile an interactive CLI or TUI without external services. Use for CLI UX checks, startup regressions, memory leaks, hangs, prompt flows, or terminal demo |
| control-ui | Build or adapt a local browser/CDP harness to drive and inspect a web, IDE, or Electron UI. Use for local UI verification, screenshots, accessibility snapshots, perf profiles, visual diffs, or reproducing UI bu |
| create-verification-skill | Generate a project-local verification skill that drives your app the way a user does — any language, framework, or platform. Use for /create-verification-skill, \"make a control skill for this repo\", or when a |
| deslop | Remove AI-generated code slop and clean up code style |
| figure-it-out | Design an auditable playbook when no narrower one fits: a large migration, an ambitious multi-part change, or work a human reviews after stepping away. Scales rigor to the task, runs a hypothesis loop, and logs |
| fix-ci | Find failing PR checks, inspect logs or external check links, and apply focused fixes |
| fix-merge-conflicts | Resolve merge conflicts non-interactively, validate build and tests, and finalize conflict resolution |
| get-pr-comments | Fetch and summarize review comments from the active pull request |
| how | Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). E |
| interrogate | Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Multiple LLM reviewers challenge changes fro |
| loop-on-ci | Monitor PR checks and fix failures until green. Uses gh pr checks as the source of truth for PR-attached checks. |
| maintain-verification-skill | Periodic pass that keeps a project's verification skill and feature map honest: parallel source readers per feature, one live session driving every feature, at most one PR of proven corrections. Use for /mainta |
| make-bot-ui | Build a local UI or authenticated webhook that starts a configured pstack background worker, keeping the sender key out of the browser and chat. |
| make-pr-easy-to-review | Prepare PRs for review by cleaning noisy history, improving PR descriptions, and adding reviewer guidance without changing code behavior. Use for "make this easy to review", "tidy this PR", "clean up commits",  |
| new-branch-and-pr | Create a fresh branch, complete work, and open a pull request |
| no-comments | Spawn Comment Sicko, fix accepted findings, and offer encodings for claimed constraints. |
| poteto-mode | poteto's agent style for concise, detailed responses, deliberate subagents, unslopped prose, simple code, and verified work. Use for poteto, /poteto-mode, or requests to work in this style. |
| pr-review-canvas | Generate an interactive PR review walkthrough as an HTML page. Fetches PR data via gh API, categorizes files into core vs mechanical changes, adds reviewer annotations, and renders diffs with moved-code detecti |
| principle-attack-the-premise | Apply when two or more fixes that share one premise have failed the same gate. Take a census of which actors hold the imbalance before the next fix, then question the premise instead of writing another fix that |
| principle-boundary-discipline | Apply when wiring validation, error handling, or framework adapters. Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions |
| principle-build-the-lever | Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks. Build the tool that does it or proves it (codemod, script, generator, or a skill your subagents follow) instead of working |
| principle-encode-lessons-in-structure | Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction. Encode the rule as a lint, metadata flag, runtime check, or script instead of more text. |
| principle-exhaust-the-design-space | Apply when facing a novel UI interaction or architectural decision with no precedent in the codebase. Build 2-3 competing prototypes and compare side by side before committing. |
| principle-experience-first | Apply when product, UX, or feature-scope tradeoffs come up. Choose user delight over implementation convenience; ship fewer polished features over more rough ones. |
| principle-fix-root-causes | Apply when debugging. Trace each symptom to its root cause and fix it there; reproduce first, ask why until you reach it, resist nil-check guards that silence crashes. |
| principle-foundational-thinking | Apply before writing logic: choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share. Get the data structures right so downstream code becomes obvious. |
| principle-guard-the-context-window | Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads. |
| principle-laziness-protocol | Apply when refactoring, evaluating diff size, or tempted to add abstractions, layers, or signal threading. Bias toward deletion and the smallest change that solves the problem. |
| principle-make-operations-idempotent | Apply when designing commands, lifecycle steps, or processing loops that run amid crashes, restarts, and retries. Converge to the same end state regardless of partial prior runs. |
| principle-migrate-callers-then-delete-legacy-apis | Apply when introducing a new internal API while old callers still exist. Migrate callers and delete the old API in the same wave instead of preserving compatibility layers. |
| principle-minimize-reader-load | Apply when reviewing or shaping code that's hard to trace. Count layers between question and answer, and hidden state in the reader's head; collapse one-caller wrappers and shrink mutable scope. |
| principle-model-the-domain | Apply when writing stateful logic, or when code branches a lot or repeats a shape assumption across files. Encode the domain in a structure instead of scattered conditionals. |
| principle-never-block-on-the-human | Apply when tempted to ask 'should I do X?' on reversible work. Proceed, present the result, let the human course-correct after the fact; reserve confirmation for irreversible actions. |
| principle-outcome-oriented-execution | Apply during planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture; don't preserve smooth intermediate states with throwaway compatibility code. |
| principle-prove-it-works | Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles. |
| principle-redesign-from-first-principles | Apply when integrating a new requirement into an existing design. Redesign as if the requirement had been a foundational assumption from day one, instead of bolting it on. |
| principle-separate-before-serializing-shared-state | Apply when concurrent actors might write to the same file, branch, key, or state object. Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant. |
| principle-sequence-verifiable-units | Apply to multi-step work (sweeps, migrations, runs of similar edits) and to how you stack commits and PRs. Break work into small units that each end in a verifiable state, check each before the next, and order  |
| principle-subtract-before-you-add | Apply when sequencing an addition, refactor, or rewrite. Remove dead code, redundant validators, and stub references first, then build on the simpler base. |
| principle-test-behavior-not-implementation | Apply when you write, change, or keep a test. Call the code the way its users do and assert the result they observe against a literal expected value. If the test would still pass when every imported function re |
| principle-type-system-discipline | Apply when designing types, reviewing a function signature, or writing code in any statically-typed language. Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, r |
| recall | Reconstruct your recent working context from your own chat history, live state, and the shared record (user reports, prior fixes, incidents), then hand back a tight current-state brief. Use for 'recall my work  |
| reflect | Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect. |
| review-and-ship | Review the current branch for bugs, intent fit, and test coverage; run or write tests; commit focused work; open or update a PR. |
| run-smoke-tests | Run Playwright smoke tests, debug failures, and verify fixes |
| setup-pstack | Set up pstack in the current coding environment. Detect available coding harnesses, use native agents by default, and configure optional local providers without servers, tunnels or remote laptop access. |
| show-me-your-work | Keep a reviewable decision trail for long-running or unattended work: a TSV log with one row per decision (what, why, evidence, result). Local by default; commit it when a reviewer needs the trail to trust the  |
| swarm | Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration. |
| tdd | Use only when the user explicitly asks for TDD, a failing test, or a regression test, OR when the bug has an obvious cheap local test target. Skip when the test path is unclear, expensive, integration-heavy, or |
| teach | Explain a body of work plainly so a person actually understands it. Runs the `how` and `why` skills and weaves what they find into one clear explanation. Use for 'teach me this', 'help me really understand X',  |
| team-kit-rules | Apply the two preserved cursor-team-kit engineering rules when writing code, including exhaustive TypeScript switches. |
| technical-writing | Layered technical-writing standard: Diátaxis structure, Google developer style sentences, STE instruction rules, Global English syntax. Use for /technical-writing or when writing or reviewing docs, RFCs, readme |
| thermo-nuclear-code-quality-review | Run an extremely strict maintainability review for abstraction quality, giant files, and spaghetti-condition growth. Use for a thermo-nuclear code quality review, thermonuclear review, deep code quality audit,  |
| typescript-best-practices | TypeScript best practices. Use when reading or editing any .ts or .tsx file. |
| unslop | Cut AI tells from any writing. Must always apply. |
| update-pstack | Absorb a future upstream pstack/cursor-team-kit commit into the OpenAI port with three-way merging and behavior verification. |
| verify-this | Verify a claim with fresh local evidence: restate it falsifiably, capture baseline and treatment, compare artifacts, and return VERIFIED, NOT VERIFIED, or INCONCLUSIVE. |
| weekly-review | Produce a weekly synthesis of authored commits with highlights by bugfix, tech debt, and net-new work |
| what-did-i-get-done | Summarize authored commits over a user-specified time period into a concise update |
| why | Use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Discovers available MCPs and queries each evidence category (source control, issue t |
| workflow-from-chats | Extract durable working preferences from recent Cursor chats and convert them into skills, rules, or workflow docs. Use when asked to learn preferences, mine feedback, personalize workflows, or generate team/pe |

## Playbooks, agents, configuration and dependencies

All 23 playbooks retain their original numbered procedures and principle references. Mode routing and durable step extraction are tested for every book. The fresh installed native run exercised investigation and recovery; the remaining books use the shared mechanisms with the individual limits below.

| Playbook | Native implementation and verification limit |
| --- | --- |
| authoring-a-skill | Host skill authoring plus actual validation; no new project skill tested here |
| autonomous-run | Host continuation, explicit predicate and stop/cancel limits; native idle wake needs a scheduler |
| autopilot-full | Original complete sequence with native checkpoints and verification; full application run untested |
| autopilot-stack | Frozen bottom-to-top GitHub order and exact-head gates; actual stack shipping untested |
| babysit | Native GitHub/gh checks and review remediation; historical read/watch evidence, no authorized mutation target |
| bug-fix | Reproduce, native fix, actual proof; prior optional CLI repair receipt is historical |
| eval | Blinded rubric and evidence preserved; project-specific evaluation untested |
| feature | Native exploration, architecture, implementation and verification; application-specific run untested |
| hillclimb | Explicit metric, iteration budget and real measurement; metric target not supplied |
| investigation | Fresh installed native run completed with real verification and recorded skipped steps |
| multi-phase-plan | Durable dependency units and decisions; project-specific plan not supplied |
| opening-a-pr | Current host Git/PR integration and attachment; actual PR creation not tested |
| orchestrate | Original Bun units/inbox/gates/ledger and GitHub frontier adapter; existing runtime tests |
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
| Cursor manifest/skills/agents/rules | Root manifest plus native Codex manifest, 71 discovered skills, optional trusted lifecycle bridge; no MCP/app registration |
| pstack-models.mdc, user model prompts, speed/reasoning suffixes | Persistent SQLite configuration with explicit role/budget choices and exact host identifiers; no guessed Cursor model IDs |
| Task/TodoWrite/background/update_state | Native agent/plan/continuation tools plus durable tasks and checkpoints; actual host restrictions apply |
| create-skill/context-loader/history | Native skill authoring and scoped task history; no unrelated personal transcript scan |
| Python and SQLite | Python 3.11+ and standard library for helpers; installed tests ran under Python 3.12; interpreter required in the executing environment |
| Bun and Commander | Original orchestration/watch tools and pinned Commander 14 retained; historical 52 upstream tests; Bun needed when those scripts run |
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

Every original source/configuration/template/asset is listed with its path and SHA-256 in `upstream-inventory.json`: 187 original files remain byte-identical. Git records adapter changes separately; tools/check_upstream.py verifies originals. Inventory and preserved instructions alone are not behavioral proof.
