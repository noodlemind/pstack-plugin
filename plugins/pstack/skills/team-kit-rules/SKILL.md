---
name: team-kit-rules
description: Apply the two preserved cursor-team-kit engineering rules when writing code, including exhaustive TypeScript switches.
---

Read [the execution contract](../../references/runtime-contract.md). Use the current host native tools; cloud uses available OpenAI models. No laptop connection, URL or MCP setup.


# Team kit rules

Keep imports at module top. A strict circular dependency exception must be documented.
For TypeScript discriminated unions and enums, put a `never` check in switch default so new variants fail compilation until handled.

Original Cursor alwaysApply rules are preserved verbatim under `upstream/cursor-team-kit/rules`. The trusted local lifecycle hook injects these rules into sessions; the worker contract applies them to detached jobs. When hooks are unavailable, invoke this skill explicitly. No global rule injection is claimed on a cloud executor without hooks.
