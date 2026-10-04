# Work tracking

This repository is the canonical source for the independent port. Git commits record implementation history, pull requests record future reviews, and issues track remaining behavior work. The archived upstream pin is not silently advanced.

The [existing-port comparison](docs/existing-ports.md) records prior art. The [product direction](docs/product-direction.md) defines the value this adaptation must prove. Reuse reviewed upstream improvements and propose generally useful changes to their original projects. Another copy of the skills is not the release objective.

## Current baseline

- Native execution policy; no remote computer bridge or public endpoint.
- Explicit first-user budget selection, persistent changes and preserved existing preferences.
- Original source/license inventory and reviewed upstream update mechanism.
- Source-only public distribution, staged-tree privacy checks and reproducible verification.

## Incomplete work

| Work item | Acceptance criteria |
| --- | --- |
| [Upstream 0.15.9 reconciliation](https://github.com/noodlemind/pstack-plugin/issues/4) | Compare the current pin with `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`; account for every change, including correct and benchmark-checklist; preserve adaptations, run behavioral checks, then advance the pin |
| [Streamlined setup and CLI compatibility](https://github.com/noodlemind/pstack-plugin/issues/5) | One setup flow reports installed, selected and verified states separately; no fresh-user defaults or silent substitutions; supported CLI versions pass discovery, execution, cancellation and recovery tests without widening host permissions |
| [Live cloud validation](https://github.com/noodlemind/pstack-plugin/issues/8) | Install in an actual supported cloud host; run setup, native work, real verification, durable checkpoint export and interrupted recovery; record available models and permissions without personal data |
| [Native agent coordination and continuation](https://github.com/noodlemind/pstack-plugin/issues/7) | Exercise real native spawn/reuse/message/cancel and arena/swarm behavior in a host that permits delegation; verify idle wake, stop conditions and cancellation through its supported scheduler |
| [Direct provider APIs and OpenRouter](https://github.com/noodlemind/pstack-plugin/issues/6) | Explicit opt-in per executing environment; protected secret storage; actual model/effort discovery and probes; explicit OpenRouter routing and no silent fallback; no laptop relay; verified cancellation, recovery and provider-diverse review; SDK compatibility alone is insufficient |
| [Benny team workflows](https://github.com/noodlemind/pstack-plugin/issues/9) | Supply project/channel/trusted identity/tracker and budgets; verify exact scheduled connector access, two real reproductions, idempotent original-thread delivery, rejection/ownership gates and bounded draft behavior |
| [Shipping integration](https://github.com/noodlemind/pstack-plugin/issues/10) | Authorized disposable PR target; verify exact pushed head, remediation, independent review, CI, cancellation and explicit shipping authority |

These are intentionally incomplete. No external account, posting permission, model entitlement or continuous execution facility is inferred from an installed package. See coverage for current evidence and limits.
