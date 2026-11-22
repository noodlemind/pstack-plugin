# Set up pstack

In this page you install the plugin, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

Follow the [Codex installation instructions](../../references/first-use.md) in the environment that will run the plugin. Start a fresh chat and ask: “Set up pstack for this environment.”

## Pick your models

The [setup skill](../../skills/setup-pstack/SKILL.md) asks for a reasoning budget of small, medium, large, or unlimited. A fresh installation has no selected budget. These names set effort targets within the current host’s supported levels. They do not grant provider access. You can change the budget later, and existing explicit choices are preserved.

Native execution uses the models and tools your host exposes. If it cannot select an agent model, record inheritance. Record any missing provider diversity when comparing approaches. Local coding CLIs are optional and require explicit environment-local selection and verified access. Keep the panel as small as the problem allows.

## Add project verification

When there is no harness that drives the product, [create a verification skill](../../skills/create-verification-skill/SKILL.md). For an invariant that tests rarely exercise, such as retries never processing a job twice, [create a formal verification skill](../../skills/create-formal-verification-skill/SKILL.md). Setup offers these when relevant. Choose them independently. See [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) for a worked example.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt.

Continue with normal follow-ups. Ask to keep poteto-mode active for this session or explicitly request workspace scope. The [native runtime contract](../../references/runtime-contract.md) explains how to recover mode and tasks after interruption.

Next: [Route work through `/poteto-mode`](./02-poteto-mode.md).
