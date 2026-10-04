# Product direction

This adaptation aims to make Lauren Tan's pstack practical across Codex environments with one setup flow and evidence that its workflows work. Stable operation and simpler setup are acceptance goals. They are not claims of superiority over existing ports.

The independent repository remains useful if it reduces the work users do to choose, configure and recover their execution environment. [Other ports](existing-ports.md) already solve many of these problems. We will reuse reviewed improvements, keep their attribution when importing code, and avoid rebuilding working tools merely to own an implementation.

## One setup flow, explicit execution choices

Setup reports the current environment and passively finds known coding CLIs. Finding an executable does not authorize running it, prove login, or prove access to any model. A new user chooses reasoning effort. Existing user choices survive upgrades. Project-level instructions and personal installation can coexist without copying credentials into a repository.

| Execution choice | Intended behavior | Current status |
| --- | --- | --- |
| Native Codex or a compatible Work coding host | Use tools and models exposed by the executing host; remain usable without other providers | Implemented; local evidence and cloud gaps appear in coverage |
| Optional local coding CLI | Invoke only selected, supported harnesses on the current machine; verify the requested model and supported operations | Adapters exist; access is environment-specific and requires setup |
| Direct provider API | Call the selected provider from the executing environment with its own credentials, model selection and limits | Planned; disabled |
| OpenRouter API | Select the requested model and routing policy explicitly; record the actual reported endpoint and model when observable | Planned; disabled |

Cloud execution defaults to its available OpenAI models. A future cloud API adapter would make outbound requests from the cloud environment. No mode requires a hosted plugin service, inbound laptop access, tunnel, or shared desktop login session.

## Common behavior does not imply identical capabilities

A coding CLI may own tools, workspace permissions and a resumable session. A model API provides inference and may require our application to own the tool loop. An API adapter therefore needs actual tool-execution and interruption tests before it can replace a coding harness. An OpenAI-compatible request format does not prove equivalent reasoning, tool calls, cancellation, or recovery.

The compatibility record must distinguish discovery, authentication, successful inference, tool execution and recovery. It must preserve the requested model and effort, observable reported identity, stop reason, verification evidence and any capability gap. Secrets stay in the executing environment's protected storage. They never enter versioned profiles, prompts, receipts or upstream snapshots.

OpenRouter documents explicit provider selection and disabling routing fallbacks. The future adapter must make that choice visible and prevent an unavailable panel seat from silently becoming a different model. See [OpenRouter provider selection](https://openrouter.ai/docs/guides/routing/provider-selection). Multiple model families accessed through OpenRouter can provide model diversity; one gateway is not independent transport, and repeated calls to one model are not a diverse panel.

Reasoning effort, maximum concurrent workers, elapsed runtime, token limits and spending controls are separate choices. The current small/medium/large/unlimited labels select reasoning effort only. Future API spending controls must state what they enforce and what they can only estimate.

## Release evidence

A supported execution path needs repeatable evidence for the following behavior:

- Fresh setup makes no hidden model, budget or provider choice. Reconfiguration and upgrade preserve unrelated settings.
- Requested models and efforts are validated against the current environment. Failed access remains visible.
- Parallel work has explicit ownership. Missing workers and disagreements survive synthesis.
- Cancellation stops owned work. Timeouts and interrupted responses produce unfinished states, not success.
- A new process can recover the task and recheck its repository revision, pending operations and verification evidence.
- Verification executes the relevant project behavior. An exit code, manifest or model response alone does not prove the product works.
- A stopped host does not claim continued execution. Scheduled continuation needs an observed wakeup and a verified stop condition.

These checks should become reusable fixtures across native, CLI and API implementations. Provider access tests run only with explicit environment-local setup. Public CI uses synthetic fixtures and cannot certify a user's account access.

## Maintenance boundary

Lauren's workflows and principles remain the content upstream. Compatibility code, setup and behavior tests belong to this repository. Keep a pinned source inventory and review every changed workflow before upgrading. The comparison with other ports is a source of reusable work, not permission to copy their code without provenance or assume their integration reports apply here.

Direct APIs and OpenRouter remain a separate development stage. Adding provider names to a menu will not close that stage. The roadmap requires live access, tool execution, cancellation and recovery evidence before support is advertised.
