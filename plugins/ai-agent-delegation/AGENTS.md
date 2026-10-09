# ai-agent-delegation

This plugin owns explicit handoff instructions and a thin external Bridge client.
Read the repository AGENTS.md first. Keep the plugin independent of CodeVow.

- Behavioral changes require a meaningful failing test before implementation.
- Do not embed runtime, engine drivers, credentials, task state or installation.
- Preserve explicit target engines and exact task/session identities.
- Current-user intent is context to check, not a machine-verifiable human identity.
  Neither `approved=true` nor Agent-written receipts grant authority.
- Keep three host adapters skills-only. Host behavior stays `unverified` until
  source/package-bound real host evidence exists.
- Register each public resource explicitly in product.json; links must be portable.
- Do not commit, push, tag, install, publish or alter global host configuration.
