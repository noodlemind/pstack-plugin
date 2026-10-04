# First use

1. Install pstack through the supported plugin flow and start a fresh chat. Say **“Set up pstack for this environment.”** The host must support local skills/helper execution; a desktop install does not install the plugin in a separate cloud environment.
2. Setup detects known coding harnesses without running them or reading their credentials. Native host tools are selected as the execution method. No reasoning budget, model identity or optional coding harness is selected for a new user.
3. Choose a reasoning budget when asked: **small** targets medium effort; **medium** targets high; **large** targets xhigh; **unlimited** targets max. Actual effort is limited by the selected host model's verified/advertised support. These names are not spending caps, token allowances or execution-time limits. Work that needs model planning waits for this choice.
4. Read back the choice and run one real project verification command. Say **“Use poteto-mode to implement and verify this change.”** After an interruption say **“Use pstack to recover this work.”**

To change your choice later, say **“Change my pstack reasoning budget to small.”** Setup preserves an existing choice when no change is requested. One user's configuration is never bundled into another user's installation. Per-role models are chosen only from actual host metadata, with explicit preference changes; unknown model access is reported as a gap.

For manual local setup, from this repository:

```sh
python3 plugins/pstack/runtime/pstack.py setup --host local
python3 plugins/pstack/runtime/pstack.py setup --host local --budget small
python3 plugins/pstack/runtime/pstack.py call pstack_environment preferences '{}'
```

The first command reports `requires_budget_choice: true` for a fresh user. The second is an explicit user choice; replace `small` with your preference. In a cloud host use `--host cloud`; do not copy a local machine's configuration or logins there. If the host does not expose model selection or native scheduling, the plugin reports that limit.

Python 3.11+ and Git are required for helpers and verification. Bun is needed for the preserved orchestration/watch tools; install their dependencies from the bundled lockfile before using them. Node 20+, Playwright and a browser are needed only for optional local browser controls. Host-native browser/terminal tools remain preferred. The source repository excludes installed dependencies.

## Personal or project use

The repository marketplace file points at `plugins/pstack`. The personal installer copies the bundle into the user's plugin source and preserves other marketplace entries. For project use, keep the complete bundle under the project's `plugins/pstack` and add/merge its entry into that project's `.agents/plugins/marketplace.json`; do not replace an existing marketplace or change its name. Enable `pstack@<that-marketplace-name>` through the host's trusted project configuration. Repo discovery/enablement and available hooks still depend on the host.

Configuration is user/environment state, not a committed default. It normally lives in `~/.local/share/pstack`. To deliberately isolate state for a project, set `PSTACK_DATA` to an ignored private project directory in that execution environment. Never commit the resulting state. Optional local CLI choices are machine-bound and require a supported adapter plus actual authentication/model checks. Cloud mode cannot use those local adapters.

If hooks are unavailable or untrusted, explicitly read pstack context at task/recovery boundaries; do not bypass hook review. The plain ChatGPT web interface or a cloud host without executable helpers cannot be assumed to provide this runtime. Live cloud end-to-end validation is still a tracked gap.
