# AIfordable and Runner MCP

Runner MCP is an AIfordable project.

AIfordable is the umbrella brand for software built around three practical goals:

> Secure software. Built with AI. Fairly priced.

Runner MCP keeps its own product name, repository name, CLI name, security model and release history. The Python distribution is published as `aifordable-runner-mcp` because the shorter `runner-mcp` PyPI project name is not available for a new project.

## Branding rules

Use AIfordable as a light project signature, not as a replacement for the Runner MCP product identity.

Preferred wording:

- `Runner MCP — an AIfordable project`
- `Built as an AIfordable project`
- `Secure software. Built with AI. Fairly priced.`

Do not:

- rename the `runner-mcp` command;
- mix private infrastructure details from other AIfordable projects into this repository;
- imply that AIfordable is a legal company or registered trademark unless that becomes true and is documented separately;
- add tracking, telemetry or paid services merely for branding or promotion.

## Cross-project rule

Each AIfordable product remains independently understandable and usable.

Cross-project links may help people discover other tools, but they must never create a runtime dependency between unrelated products. Security boundaries, credentials, deployment configuration and user data remain separate per product.

## Runner MCP story

Runner MCP was created from a practical constraint: routine AI-assisted development needed a safer and more predictable path to self-hosted projects than a general-purpose remote-control channel.

The design response is intentionally narrow:

- GitHub remains the collaboration and source-code surface;
- Runner MCP remains the local execution and safety boundary;
- clients choose from explicit projects and predefined operations;
- arbitrary shell input is not the normal interface;
- higher-risk operations keep separate approval gates.

That engineering story should stay more prominent than umbrella branding.
