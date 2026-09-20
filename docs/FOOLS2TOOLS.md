# Fools2Tools and Runner MCP

Runner MCP is a Fools2Tools project.

Fools2Tools is the umbrella identity for practical software that starts from a real problem and turns it into a reusable tool. Runner MCP keeps its own product name, repository name, package name, security model and release history.

A simple public description is:

> Practical tools from real problems.

For Runner MCP, the problem is concrete: an AI client should be able to help with real development and staging work without being handed a general remote shell.

## Branding rules

Use the Fools2Tools name as a light project signature, not as a replacement for the product identity.

Preferred wording:

- `Runner MCP — a Fools2Tools project`
- `Built as a Fools2Tools project`
- `Practical tools from real problems`

Do not:

- rename the Python package or command to Fools2Tools;
- mix private infrastructure details from other Fools2Tools projects into this repository;
- imply that Fools2Tools is a legal company, registered trademark or commercial service unless that becomes true and is documented separately;
- add tracking, telemetry or paid services merely for branding or promotion.

## Cross-project rule

Each project remains independently understandable and usable.

Cross-project links may help people discover other tools, but they must never create a runtime dependency between unrelated products. Security boundaries, credentials, deployment configuration and user data remain separate per project.

## Public story

Runner MCP was created from a practical constraint: routine AI-assisted development needed a safer and more predictable path to self-hosted projects than a general-purpose remote-control channel.

The design response is intentionally narrow:

- GitHub remains the collaboration and source-code surface;
- Runner MCP remains the local execution and safety boundary;
- clients choose from explicit projects and predefined operations;
- arbitrary shell input is not the normal interface;
- higher-risk operations keep separate approval gates.

That engineering story should stay more prominent than branding.
