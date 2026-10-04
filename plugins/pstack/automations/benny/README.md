# benny

## OpenAI host mapping

Before any setup or run, call the installed `pstack_context` with the target workspace and read its returned `adapter_contract` path. This remains valid after copying this pack into a repository. The OpenAI contract supersedes Cursor host syntax below while retaining the original engineering sequence.

Use the host's supported automation editor/tool for the two explicitly requested schedules. Use native project plugin settings and fresh project-rooted discovery; never create Cursor settings. Preserve user configuration outside this pack. The native coordinator owns authorized Slack/tracker delivery; workers have no posting integration. Explicitly choose all four Benny model roles from live-probed provider:model keys and all eight execution budgets. Template values are proposals to review, not completed setup. Keep this pack dormant until real connector/thread/control preflight and activation tests pass.


benny gives you two cursor automations for slack issue reports. one triages each report. the other reproduces confirmed bugs and may prepare a small draft fix.

the files in this directory are dormant setup and automation sources. they do not appear as slash skills.

## set it up

1. point cursor at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.
2. let setup merge this whole directory into the target at `.agents/automations/benny/`. it must preserve destination-only files and review conflicts instead of overwriting local edits.
3. let setup enable pstack in the target repository's `.codex/config.toml` for shared dependencies:

```toml
[plugins."pstack@<actual-personal-marketplace-name>"]
enabled = true
```

4. keep user-owned configuration outside the copied pack, for example in `.agents/benny/`. adapt [`configuration.example.yaml`](./templates/configuration.example.yaml) and [`feature-map.example.md`](./skills/reproduce-and-fix-issues/references/feature-map.example.md).
5. commit `.codex/config.toml`, `.agents/automations/benny/`, and any secret-free configuration before enabling either automation.
6. review each new automation draft or update existing automations in their editors. then send a harmless test report and verify every source-channel post stays in the original thread.
