---
name: update-pstack
description: Absorb a future upstream pstack/cursor-team-kit commit into the OpenAI port with three-way merging and behavior verification.
---

Read [the execution contract](../../references/runtime-contract.md). Use the current host native tools; cloud uses available OpenAI models. No laptop connection, URL or MCP setup.


# Update pstack

Read references/upstream-updates.md for the exact commands and review gates.

1. Read the installed pin, adapter identity and behavior coverage table. Fetch the official repository into a separate checkout and resolve the requested ref to an exact commit.
2. Plan both pstack and cursor-team-kit changes with runtime/upstream_sync.py. Inspect every changed skill, agent, playbook, configuration mechanism, runtime and dependency. Byte compatibility does not establish behavior equivalence.
3. Stage a separate candidate. Compatible port edits merge; conflicts remain beside preserved current files. Adapter-owned setup, bot UI, manifests and licenses require review. Live installation, configuration, credentials, hook trust and marketplace remain untouched during plan/stage.
4. Resolve conflicts and implement changed behavior. Update role catalogs only from actual model access and explicit user choices. Preserve attribution and license. Revise coverage with real evidence and remaining gaps.
5. Run adapter/upstream tests and native candidate workflows through a separate named candidate installation. Include roles/config persistence, diverse panels, reuse, continuation/cancellation, real verification and interrupted recovery. Record exact-pin review/evidence in UPDATE-REVIEW.json; do not mark skipped tests passed.
6. Install the reviewed candidate through runtime/install.py. Drain active jobs or explicitly pause/recover before restarting the service. Read back installed pin and native tool results. Trust changed hooks through the host's review flow.
7. On failure, retain the existing installed pin. The saved old upstream snapshot and package allow rollback through the installer; do not roll back user configuration or runtime state as a package side effect.
