# Security Policy

## Supported use

GapForge is a **research / educational** tool. It must not be used for clinical decision-making or as sole evidence for regulatory submissions.

## Reporting vulnerabilities

Please open a private security advisory on GitHub or email the maintainer via the profile on [github.com/LordKay-sudo](https://github.com/LordKay-sudo).

Do not file public issues for vulnerabilities that could enable:

- Injection into Neo4j / API without auth (deployments should not expose Neo4j publicly)
- Prompt-injection paths that bypass L3 blocks or forge approved review status
- Leakage of credentials from `.env` examples (never commit real secrets)

## Deployment guidance

- Keep Neo4j and APIs on private networks or behind auth
- Set strong `NEO4J_PASSWORD`
- Treat MCP agents as **propose-only**; require UI HITL for L2 conclusions
- Pin model and data versions in exported review bundles
