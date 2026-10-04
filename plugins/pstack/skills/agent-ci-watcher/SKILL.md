---
name: agent-ci-watcher
description: Watch PR CI for the current branch and report pass/fail with relevant failure links. Use when waiting for CI results or CI has failed. Use proactively to monitor branch CI.
---
## OpenAI runtime contract

Read [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host by default. Cloud uses its available OpenAI models. No remote laptop connection, server URL or MCP setup is permitted. Optional local CLI adapters require explicit environment-local selection. Do not claim cross-provider diversity for OpenAI-only review.


# CI watcher

CI monitoring specialist for PR-attached checks.

## Trigger

Use when waiting for CI results, CI has failed, or when proactively monitoring branch CI.

## Workflow

1. Determine current branch: `git branch --show-current`
2. Resolve the PR: `gh pr view --json number,url,headRefName`
3. Inspect attached checks: `gh pr checks --json name,bucket,state,workflow,link`
4. If checks are pending, watch: `gh pr checks --watch --fail-fast`
5. If a GitHub Actions check failed, fetch logs with `gh run view <run-id> --log-failed`; otherwise, return the check link and concise next step.

## Output

- CI status (passed/failed)
- PR and check metadata
- If failed: concise failure excerpt or external check link and likely next step
