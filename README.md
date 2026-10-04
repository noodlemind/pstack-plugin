# pstack for Codex

An independent, experimental Codex adaptation of **[pstack by Lauren Tan (poteto)](https://github.com/cursor/plugins/tree/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack)**. Lauren's engineering principles and workflows are the foundation; this repository supplies host compatibility, explicit setup, durable state, verification helpers and a reviewable update path. [Attribution and licenses](NOTICE.md).

The intended value is consistent, verifiable operation across coding environments. Native host tools work by default; supported local CLIs require explicit selection. Direct provider APIs and OpenRouter are planned, not available in this release. Passing local tests does not establish full upstream equivalence or greater reliability than another port.

## Do you need this port?

If you use Cursor and upstream pstack already meets your needs, use the [original plugin](https://github.com/cursor/plugins/tree/main/pstack). You do not need this port simply to keep instructions in a repository.

Several [existing unofficial ports](docs/existing-ports.md) already provide Codex workflows, native agents, recovery and, in some cases, external CLI execution. This project does not claim to be the first or the official Codex port. Its [development scope](docs/product-direction.md) concentrates on setup, execution boundaries and repeatable behavior checks. Plugin packaging makes related skills and helpers installable and versioned together. It is a distribution choice, not a requirement for every project.

| Choice | Appropriate use |
| --- | --- |
| Original pstack in Cursor | Native Cursor workflows with upstream support and updates |
| Repository skills / instructions | One project's conventions and procedures; maintain any required helper/runtime wiring yourself |
| This plugin, personal install | Reuse the adapted workflows across your projects |
| This plugin, repository marketplace | Pin and review the complete bundle for one team/project |

Codex supports [repository skills](https://learn.chatgpt.com/docs/build-skills) and [repository or personal plugin marketplaces](https://developers.openai.com/plugins/build/plugins). These approaches can coexist; installing the same skill twice can produce duplicate discovery.

## Get started

Clone this repository. To install the bundle into your personal Codex marketplace while preserving other entries:

```sh
git clone https://github.com/noodlemind/pstack-plugin.git
cd pstack-plugin
python3 plugins/pstack/runtime/install.py
```

This uses the supported Codex marketplace/installation commands. It does not choose a reasoning budget, enable another coding CLI, change global model defaults or trust hooks automatically. Review hooks through the host when requested. Start a fresh Codex chat and say:

> Set up pstack for this environment.

Setup asks for **small, medium, large or unlimited** reasoning. There is no selected budget for a new user. Existing explicit choices are retained, and “Change my pstack reasoning budget to small” updates the saved choice. The names describe reasoning effort, not a spending limit, token allowance or promise of unlimited runtime.

Then say “Use poteto-mode to implement and verify this change.” After an interruption, say “Use pstack to recover this work.” See [first use](plugins/pstack/references/first-use.md) for manual setup, project scoping, dependencies and limitations.

## Execution and privacy

Native tools in the current host are the default. Setup passively detects coding harnesses; optional supported local CLIs require the user's choice and verified access. There is no MCP server, tunnel, public endpoint, login service or cloud-to-laptop bridge. External model APIs are disabled pending a separate explicit provider flow.

The repository contains source and synthetic tests, not personal configuration, provider logins, transcripts, screenshots, session IDs or private verification exports. Local runtime state stays outside the plugin cache; treat that state as private. Read [security and privacy](SECURITY.md) before contributing artifacts.

## Status and development

Adapter version **0.15.5-openai.7** pins upstream **0.15.5** at `7022c81efb48d8b5eb15498ce6043a3bd74b694c`. The bundle preserves 71 skills, 23 playbooks, four agent roles and the Benny automation procedures. Preservation alone does not establish full behavioral equivalence. Upstream **0.15.9** was verified during the comparison; importing that newer behavior remains a reviewed update task.

[Coverage](plugins/pstack/references/behavior-coverage.md) distinguishes tested behavior from live cloud, native scheduling, cross-provider and team-integration gaps. [Verification](docs/verification.md) describes reproducible checks. [Roadmap](ROADMAP.md) and GitHub issues track remaining work. [Contributing](CONTRIBUTING.md) explains reviews and releases; [upstream updates](plugins/pstack/references/upstream-updates.md) explains how to absorb changes without discarding the port.
