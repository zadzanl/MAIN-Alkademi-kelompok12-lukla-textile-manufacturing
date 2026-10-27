# Backend Agent Guidelines & Security Memo

## Copilot Secret Policy

OpenRouter credentials must be supplied at runtime through `COPILOT_API_KEY` or
`OPENROUTER_API_KEY`; source files and deployment templates must not contain
secret values. `COPILOT_API_KEY` takes precedence when both variables are set.
The free model default remains `nvidia/nemotron-3-super-120b-a12b:free`.

For AWS EC2, set `COPILOT_DEFAULT_PROVIDER="bedrock"` to use the attached IAM
role without an API key, or configure an OpenRouter key in the deployment
environment. Missing OpenRouter credentials produce an actionable configuration
error and must not trigger paid external calls.
