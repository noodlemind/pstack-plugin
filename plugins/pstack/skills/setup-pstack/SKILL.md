---
name: setup-pstack
description: Set up pstack in the current coding environment. Detect available coding harnesses, use native agents by default, and configure optional local providers without servers, tunnels or remote laptop access.
---

# Setup pstack

Read [the runtime contract](../../references/runtime-contract.md). Resolve this skill's plugin root; never assume a path on the user's other machines.

1. Determine the actual execution location from the current host context. Run `python3 <plugin-root>/runtime/pstack.py setup --host local` in a local desktop/CLI task, or `--host cloud` in a cloud task. If the location is unknown, use `--host auto`: native execution remains the safe default. This detects known coding harness executables without invoking them, inspecting login credentials, or starting services. A listed executable is a candidate, not authenticated model access. Unsupported adapters remain disabled.
2. Use the current host's native agent, model, shell and browser tools by default. Cloud execution always uses the available native OpenAI models and cloud workspace. Do not create a server, tunnel, public URL, laptop connection, API key, or OAuth application. No MCP setup is needed. Install/load the plugin in the actual cloud host; a desktop install alone does not establish cloud availability.
3. Read `pstack_environment preferences` through the helper. A fresh user has `budget: null` and `requires_budget_choice: true`; never interpret missing state as unlimited. Ask for small (medium effort), medium (high), large (xhigh), or unlimited (max), and wait for the user's answer. Preserve an existing explicit choice unless the user requests a change. Save the actual choice through `pstack_environment budget` with `budget` and the user's `confirmation`, or `setup --budget <choice>` after that choice. Explain that reasoning level is not a spending cap or an execution-time budget. Native model planning refuses an unconfigured budget. Do not import a maintainer's configuration, role IDs, catalog or login state.
4. Read the current host's actual model catalog/tool metadata. When exact OpenAI models and supported efforts are exposed, record them with `pstack_environment catalog`, including the real evidence source. Use `pstack_environment plan` for each role and panel. If the user specifies per-role models, persist all 17 roles through `pstack_environment configure` with model IDs from that host catalog and their actual confirmation. It retains compatible saved OpenAI preferences and clamps the selected budget to advertised supported efforts. If the host cannot select subagent models, inherit its current model and disclose that limitation. Separate reviewers on one model are different perspectives, not model diversity. All-OpenAI panels are not cross-provider panels.
5. Optional local harnesses: show the detected candidates only if useful to the user. Keep them disabled unless the user chooses them. An explicit prior choice applies on the same machine; do not ask twice. Enable selected supported adapters with `setup --host local --enable-cli <id> --confirmation <user choice>`. Discover only those selected providers and live-probe exact models before storing their role choices. Missing login or unsupported tools leave that adapter unavailable; native execution is still usable. Cloud tasks never import this local selection, credentials, sockets or sessions.
6. Read back `pstack_environment scan` from a fresh process. Verify one real project command and save a scoped checkpoint. Report execution location, selected host/harness, model visibility, budget, and any reduced behavior in plain language. A harness scan or model catalog is not an inference or end-to-end verification result.

`pstack_*` names here are helper operations, not required MCP tools. Invoke them through the host's ordinary shell tool:

```text
python3 <plugin-root>/runtime/pstack.py call pstack_environment scan '{}'
```

The retained original setup procedure is at `../../upstream/pstack/skills/setup-pstack/SKILL.md`. Current environment policy overrides its Cursor-specific defaults and automatic provider substitutions.
