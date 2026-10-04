# Changelog

## 0.15.9-openai.8

- Import upstream pstack 0.15.9 at `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`; preserve all 190 originals and both MIT notices.
- Add correct, benchmark-checklist and Explain the Number; update all changed agent, design, performance, planning and PR procedures.
- Map fresh-agent reuse limits and hourly audits to the native host. Add macOS measurement guidance without enabling a scheduler or external provider.
- Preserve the adapter homepage during updates, synchronize runtime package versions, and exclude dependencies and stale staging metadata.
- Preserve full source inventory metadata, including reference lists, skill descriptions and playbook steps, in future update plans.
- Add release consistency checks and hourly plan regression tests. Record the complete change review and installed verification in `docs/upstream-0.15.9.md`.

## 0.15.5-openai.7

- Make mocked-provider fixtures independent of coding CLIs installed on the test machine. Clean Linux/macOS CI exposed six tests that depended on local executable presence.
- Preserve the production guard that rejects a missing selected CLI. Fixture launchers cannot invoke a real model account.
- Link the behavior roadmap to repository work items.

## 0.15.5-openai.6

- Establish a source-only public repository with preserved upstream credit and MIT notices.
- Require an explicit reasoning-budget choice for fresh native model planning; report unconfigured state rather than selecting unlimited or inheriting an unspecified budget.
- Add setup budget selection and accurate readback after changing an existing budget.
- Add contributor/security guidance, repository privacy checks, CI, synthetic first-use verification and tracked capability gaps.
- Record a pinned comparison with existing ports and the intended native, optional CLI and future API execution scope. No API provider or public endpoint is enabled.

## Earlier private adaptation

The native execution design, pinned original sources, optional local adapters, persistent state, verification and update machinery were developed and tested before this repository was created. Private development transcripts and account-specific artifacts are deliberately not imported into Git. This repository does not claim to reconstruct that prior commit history.
