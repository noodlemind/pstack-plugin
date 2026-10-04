---
name: fix-ci
description: Find failing PR checks, inspect logs or external check links, and apply focused fixes
---
## OpenAI runtime contract

Read [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host by default. Cloud uses its available OpenAI models. No remote laptop connection, server URL or MCP setup is permitted. Optional local CLI adapters require explicit environment-local selection. Do not claim cross-provider diversity for OpenAI-only review.


# Fix CI

## Trigger

Branch or PR CI is failing and needs a fast, iterative path to green checks.

## Workflow

1. Resolve the active PR and inspect `gh pr checks --json name,bucket,state,workflow,link`.
2. Inspect failed jobs and extract the first actionable error. Use GitHub Actions logs when available; otherwise use the check link to identify the failing command or service.
3. Apply the smallest safe fix.
4. Push, re-check the PR check set, and repeat until green.

## Guardrails

- Fix one actionable failure at a time.
- Prefer minimal, low-risk changes before broader refactors.
- Keep `gh pr checks` as the source of truth for overall PR CI state.

## Output

- Primary failing job and root error
- Fixes applied in iteration order
- Current CI status and next action
