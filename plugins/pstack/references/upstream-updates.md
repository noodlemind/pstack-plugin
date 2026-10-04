# Absorb upstream changes

The canonical adaptation is this Git repository. Preserve the exact pin in UPSTREAM.lock.json and the byte-identical originals under upstream/. Do not follow upstream main automatically or overwrite installed personal edits.

1. Fetch https://github.com/cursor/plugins into a separate checkout and resolve a desired ref to an exact commit. Inspect both pstack and cursor-team-kit changes and dependencies.
2. Run `python3 plugins/pstack/runtime/upstream_sync.py plan --repo <upstream-checkout> --ref <exact-ref> --out <private-plan.json>`. Planning reads Git blobs without executing incoming code.
3. Stage with `python3 plugins/pstack/runtime/upstream_sync.py stage --plan <private-plan.json> --destination <new-candidate-directory>`. The three-way merge preserves compatible adapter edits and leaves conflicts for review. Never stage over the active package.
4. Resolve conflicts and semantic changes, including new skills, model/provider assumptions, configuration, hooks and automations. Preserve attribution, the native execution boundary, explicit budget choice, API opt-in rules and retirement records. Do not add a laptop connection to compensate for a missing host capability.
5. Test the candidate from a separately named marketplace entry and isolated private PSTACK_DATA directory. Record actual installation, fresh setup, coordination, verification and recovery evidence. Disclose unavailable host behavior. Review changed hooks through the host.
6. Add candidate UPDATE-REVIEW.json for the exact incoming commit, with resolved_conflicts, behavior_review and installed_workflow_evidence. Use sanitized repository-relative public summaries, never personal transcripts or absolute host paths. The installer requires this record when changing the pin; the record does not prove its prose automatically.
7. Update source hashes, coverage, version and changelog; open a PR linked to the update issue. Drain or pause active optional local work before installation. Use the supported installer, preserve user state/other marketplace entries, and verify the installed result.

Package rollback does not roll back user configuration or prove database compatibility. Preserve checkpoints and review migrations separately. Tests cover merge conflicts, deletions, stale plans, path escapes and preserved custom files. A previous staging trial for upstream 0.15.6 exercised absorption mechanics; it was not installed or claimed behaviorally verified.
