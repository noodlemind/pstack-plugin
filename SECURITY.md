# Security and privacy

## Report a vulnerability

Use this repository's Security tab and **Report a vulnerability** for private reports when available. Do not open a public issue containing credentials, exploit targets, private code or personal transcripts. A report should identify the affected version, trust boundary, minimal synthetic reproduction and observed impact. Public issues may ask for a private reporting route without including sensitive details.

## Boundaries

Native execution runs under the current host's permissions. A workspace argument is not an OS sandbox. The plugin does not grant itself extra host permissions. It creates no public endpoint or connection back to another computer. Optional local CLI adapters are disabled until selected; their own tools, accounts and permission systems still matter. Native cloud mode excludes local CLI execution. Future APIs are disabled in this release, including direct prototype calls.

Persistent task state, decision trails and optional CLI output can contain private project information. They live in the executing environment's private data directory, outside the plugin source and cache. Do not commit that directory, install backups, provider credentials or model-access receipts. `PSTACK_DATA` can select another private directory; use an ignored project-local directory only when deliberately scoping state to that project.

## What may enter Git

Source, license notices, pinned original public upstream material, synthetic fixtures, reviewed summaries and reproducible tests are allowed. Public attribution to Lauren Tan (poteto), Cursor and this repository's public maintainer identity is intentional; it is not a reason to publish private contact details.

Real user names, home paths, personal email addresses, hostnames, session/thread IDs, account identifiers, API keys, OAuth grants, environment dumps, recordings and screenshots are excluded. Test contacts must use reserved example domains or localhost; test IDs must be obviously synthetic. Dependency directories and raw local evidence are ignored and rejected by the staged-tree audit.

The audit checks common secret formats, sensitive paths, private metadata and contact details. It reports file names and rule names, never matched secret values. Pattern scans are defense in depth, not proof that every possible secret or personal detail has been recognized. Review the exact staged tree and preserve GitHub's secret scanning/push protection when available.

## After a leak

Revoke exposed credentials before history cleanup. Removing a file in a later commit does not remove it from history, forks, caches or existing clones. Coordinate any history rewrite; do not force-push or delete other contributors' work automatically. Add a minimal regression test without reproducing the real secret.
