# Project adapters

Runner MCP uses a built-in allow-listed adapter registry for project-specific capability discovery.

Configuration cannot name a Python module, package, file or dynamic import path. Unknown adapter IDs fail closed.

Initial adapters:

- `generic`: makes no automatic assumptions and supports explicit custom presets only;
- `python`: inspects safe local Python project markers and may select existing pytest/Alembic presets when the corresponding project-local tooling exists.

Adapter inspection returns booleans and preset names only. It never returns private project or executable paths. Symlinked project markers are ignored as detection signals.

`auto` is not arbitrary command discovery. It can resolve only to a preset already implemented and allow-listed by Runner MCP. The generic adapter deliberately fails closed for `auto`.

Future adapters must be added in reviewed source code. Configuration must never become a dynamic plugin/import mechanism.
