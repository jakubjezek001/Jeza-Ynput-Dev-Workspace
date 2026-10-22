# Jeza Ynput Dev Workspace

A personal development workspace for Ynput/AYON projects. It combines Zed
tasks and `uv` scripts for working on many AYON repositories at once:
cloning them, packaging and uploading addons, running the local server and
the launcher.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/) and `git`;
[Zed](https://zed.dev/) is optional.

```bash
git clone https://github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace.git <ROOT>
cd <ROOT>
uv sync
uv run ayon-workspace bootstrap --root "$PWD"
```

Then open `<ROOT>` in Zed and run tasks from the command palette with
`tasks: spawn`. Server tools need a `.env` with `AYON_SERVER_URL` and
`AYON_API_KEY`.

## Documentation

- [Workspace layout and guardrails](docs/workspace.md)
- [Commands, Zed tasks and bootstrap](docs/workspace-tooling.md)
- [AYON development rules](docs/ayon/development-rules.md)
- [Pull request conventions](docs/pull-requests.md)

Coding agents start from [AGENTS.md](AGENTS.md).
