# Optional Grok access

Grok Build CLI is an optional local adapter and is disabled by default. Groq is a different provider. Setup may detect a `grok` executable, but executable presence is not authentication or model access. Enable it only after the user's explicit selection on that machine; discover and probe exact models/efforts before assigning roles. Preserve all other preferences and never silently substitute providers.

Local harness choices and logins are not copied into cloud tasks. Direct xAI/Grok API access remains disabled pending a separate explicit provider setup. No API-key command is available today. Future APIs must connect directly from the environment executing the task using its protected secret storage; they must not proxy through a laptop.
