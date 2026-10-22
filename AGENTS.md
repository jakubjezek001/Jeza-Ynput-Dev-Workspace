# Jeza Ynput Dev Workspace

A personal wrapper around a multi-repo AYON workspace: workspace tooling in
`src/` (run with `uv run <entry-point>`), Zed config in `.zed/`, and the
`ayon-*` repositories as gitignored clones next to them. All instructions
live in `docs/`. Read the page the task needs.

IMPORTANT: each `ayon-*` folder is its own git repository. Never commit its
content here, and never modify `ayon-backend`, `ayon-frontend` or
`ayon-docker`.

Before any development work, split the task and decide who does each part
(a script, you, or a subagent on its tier) with
[docs/subagents.md](docs/subagents.md#routing), and state the split in one
line before you start.

## Docs

- [docs/workspace.md](docs/workspace.md) — layout, guardrails, `.env` keys.
- [docs/workspace-tooling.md](docs/workspace-tooling.md) — commands, Zed
  tasks, `ayon-workspace` (repo/worktree linking, bootstrap).
- [docs/ayon/development-rules.md](docs/ayon/development-rules.md) — start
  here for any work in an `ayon-*` repo; links the repo-type pages.
- [docs/ayon/constitution.md](docs/ayon/constitution.md) — binding AYON
  addon principles.
- [docs/ayon/review-checks.md](docs/ayon/review-checks.md) — review checks
  and audit procedures.
- [docs/subagents.md](docs/subagents.md) — routing work to subagents,
  tiers, `ayon-workspace agents`.
- [docs/pull-requests.md](docs/pull-requests.md) — PR title and description.
- [docs/agent-instructions.md](docs/agent-instructions.md) — how these
  instructions are organised and how to write them.
