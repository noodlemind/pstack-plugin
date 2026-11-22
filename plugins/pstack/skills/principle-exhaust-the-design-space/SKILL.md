---
name: principle-exhaust-the-design-space
description: "Apply when facing a novel UI interaction or architectural decision with no precedent in the codebase. Build 2-3 competing prototypes and compare side by side before committing."
disable-model-invocation: true
---
## OpenAI runtime contract

Read [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host by default. Cloud uses its available OpenAI models. No remote laptop connection, server URL or MCP setup is permitted. Optional local CLI adapters require explicit environment-local selection. Do not claim cross-provider diversity for OpenAI-only review.


# Exhaust the Design Space

It also applies to product design decisions where user experience depends on feel, not logic.
