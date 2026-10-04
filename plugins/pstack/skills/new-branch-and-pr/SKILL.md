---
name: new-branch-and-pr
description: Create a fresh branch, complete work, and open a pull request
---
## OpenAI runtime contract

Read [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host by default. Cloud uses its available OpenAI models. No remote laptop connection, server URL or MCP setup is permitted. Optional local CLI adapters require explicit environment-local selection. Do not claim cross-provider diversity for OpenAI-only review.


# New branch and PR

## Trigger

Starting work that should be shipped through a clean branch and pull request workflow.

## Workflow

1. Ensure the working tree is clean or explicitly handled.
2. Create a descriptive branch from the latest main.
3. Complete implementation and tests.
4. Commit focused changes and push.
5. Create a concise PR with summary and test notes.

## Guardrails

- Keep branch scope focused on one change set.
- Include verification notes before requesting review.

## Output

- New branch name
- PR summary and test notes
- PR URL
