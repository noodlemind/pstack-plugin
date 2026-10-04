---
name: principle-subtract-before-you-add
description: "Apply when sequencing an addition, refactor, or rewrite. Remove dead code, redundant validators, and stub references first, then build on the simpler base."
disable-model-invocation: true
---
## OpenAI runtime contract

Read [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host by default. Cloud uses its available OpenAI models. No remote laptop connection, server URL or MCP setup is permitted. Optional local CLI adapters require explicit environment-local selection. Do not claim cross-provider diversity for OpenAI-only review.


# Subtract Before You Add

When evolving a system, remove complexity first, then build.

**Why:** Adding to a complex system compounds complexity. Removing first leaves less code, reveals the essential structure, and usually makes the next design obvious. Default to subtraction.

Make simplification a continual investment. Leave the design slightly simpler and more capable behind the same or smaller surface than you found it.

**The pattern:**
- Sequence removal before construction
- Cut before you polish (get to the minimum before investing in quality)
- Design for observed usage, not speculative edge cases
- No speculative validators, parsers, or guards beyond what the spec demands
- Simplify prompts (remove redundant instructions, excessive templates)
- When a reference has no novel content, delete it rather than leaving a stub
