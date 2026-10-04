# Attribution and licenses

**pstack was created by Lauren Tan, also known as [poteto](https://github.com/poteto).** This repository is an independent adaptation of [the original pstack](https://github.com/cursor/plugins/tree/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack) for Codex and compatible local ChatGPT Work coding environments. The original workflows, engineering principles, playbooks and voice are Lauren's work. The adaptation is maintained separately and is not an official Cursor, OpenAI or Lauren Tan release or endorsement.

The pinned source is `cursor/plugins` commit `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`, pstack version 0.15.9. The companion [cursor-team-kit](https://github.com/cursor/plugins/tree/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/cursor-team-kit) is credited to its original contributors and carries Copyright (c) 2026 Cursor. Its deslop, control-cli/control-ui, review procedures and two engineering rules are preserved.

| Component | Source / copyright | License record |
| --- | --- | --- |
| Original pstack | Lauren Tan (poteto), 2026 | `plugins/pstack/LICENSE`, unchanged original also under `upstream/pstack/LICENSE` |
| cursor-team-kit | Cursor, 2026 | `plugins/pstack/LICENSE.cursor-team-kit`, unchanged original under `upstream/cursor-team-kit/LICENSE` |
| Codex adaptation and repository tooling | pstack-plugin contributors, 2026 | `plugins/pstack/LICENSE.adapter` and root `LICENSE` (MIT) |
| Optional dependencies | Their respective authors | Dependency lockfiles pin versions; retain dependency license/NOTICE files when assembling binary or bundled distributions |

The root MIT license covers this source distribution without removing component notices. Original archives remain byte-for-byte intact. `plugins/pstack/UPSTREAM.lock.json` and `plugins/pstack/references/upstream-inventory.json` record the pin and all 190 source hashes. Adapter changes are tracked separately in Git; do not edit the archived originals to hide differences.

The source repository excludes dependency installations. Optional browser control uses Playwright 1.63.0 (Apache-2.0); the preserved upstream tools declare Commander 14.0.0 (MIT) plus their development dependencies. The exact package/lock files remain with those components. A release that bundles installed dependencies must include their actual licenses and notices, not only this summary.

Keep this attribution, the original copyright notices and corresponding license files when redistributing the port or substantial portions of it. Submit generally useful upstream workflow fixes to cursor/plugins where appropriate; host-specific compatibility work belongs here.
