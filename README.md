# Jeza Ynput Dev Workspace

Personal development workspace for YNPUT / AYON work, built around the Zed
editor. The workspace manages a multi-repo checkout, agent instructions,
skills and a set of Zed tasks shared across every repository and worktree.

**Task source of truth is workspace-local.** There is no
`~/.config/zed/tasks.json`; the single canonical task file is
`<ROOT>/.zed/tasks.json` and repositories/worktrees symlink to it. This
document describes the current implementation only — the previous
global-task implementation has been fully removed.

## Repository layout

```text
__YNPUT/                                  # the workspace root (<ROOT>)
  .zed/
    tasks.json                            # canonical Zed tasks (single source)
    settings.json                         # workspace Zed settings
    debug.json                            # workspace debug tasks
  pyproject.toml                          # project name: jeza-ynput-dev-workspace
  src/jeza_ynput_dev_workspace/           # uv entry points used by tasks
  .githooks-shared/post-checkout          # shared git hook (worktree setup)
  ayon-*/                                 # direct AYON checkouts
  worktrees/<addon>/<name>/<addon>/       # Zed-created worktrees

ayon-core/
  .zed/tasks.json -> ../.zed/tasks.json   # symlink to the canonical tasks

worktrees/ayon-nuke/sedge-owl/ayon-nuke/
  .zed/tasks.json -> <ROOT>/.zed/tasks.json
```

## Zed tasks

The canonical task file `<ROOT>/.zed/tasks.json` contains all 16 tasks:

| Task                                   | Type                |
|----------------------------------------|---------------------|
| Utils / Git Clone all repositories     | workspace           |
| Dev / Upload addon to server and restart | workspace         |
| Dev / Create addon package             | workspace           |
| Utils / Update AYON server             | workspace           |
| Utils / Initialize Docs                | workspace           |
| Utils / Start Docs                     | workspace           |
| Utils / Git commit info extraction     | selected repository |
| Dev / Ruff check current file          | selected repository |
| AYON / Launch App (comp)               | workspace           |
| AYON / Launch App (model)              | workspace           |
| AYON / Launch App (conform)            | workspace           |
| AYON / Launch TrayPublisher (edit)     | workspace           |
| AYON / Launcher Dev Mode               | workspace           |
| Utils / Set up new worktree            | hook (create_worktree) |
| AYON / Bootstrap agentic workspace HERE | workspace          |
| AYON / Doctor                          | workspace           |

Every task that invokes a workspace script selects the workspace project
explicitly:

```json
"command": "uv",
"args": [
  "run",
  "--project", "${AYON_WORKSPACE_ROOT:[abs path to this repository root folder]}",
  "create-addon-package",
  "-f", "$ZED_FILE",
  "--debug"
],
"cwd": "${AYON_WORKSPACE_ROOT:[abs path to this repository root folder]}"
```

This prevents `uv` from picking up `ayon-core/pyproject.toml`,
`ayon-launcher/pyproject.toml` or an addon's `pyproject.toml` instead of the
workspace project. `AYON_WORKSPACE_ROOT` may be set to override the default.

Task working-directory policy:

- **Workspace tasks** run from the workspace root: `cwd` =
  `${AYON_WORKSPACE_ROOT:...}`. They use workspace-level resources
  (`pyproject.toml`, `.env`, `ayon-docker`, `ayon-launcher`).
- **Selected-repository tasks** (Ruff check, Git commit info) run from the
  active repository/worktree: `cwd` = `$ZED_WORKTREE_ROOT`, so
  repository-specific Ruff config and Git metadata are discovered. The
  executable still comes from the workspace environment via
  `uv run --project <workspace-root>`.

File-based tasks pass `$ZED_FILE` (absolute path) as the source of truth.
Scripts resolve the actual Git checkout from that path — see "Git checkout
resolution" below.

## Per-repository and per-worktree linkage

`uv run ayon-sdd link --all` wires every in-scope repo:

- `core.hooksPath` → `<ROOT>/.githooks-shared` (absolute),
- `.agents-main` → `../ayon-agentic-instructions` (relative symlink),
- `.zed/tasks.json` → `../.zed/tasks.json` (relative symlink; creates the
  repository's `.zed/` directory if needed).

Only `tasks.json` is symlinked. Repository-owned `.zed/settings.json` and
`.zed/debug.json` are preserved.

New worktrees are wired by `uv run ayon-sdd worktree-setup`, called from
both the shared `post-checkout` hook (Git-created worktrees) and the
`Utils / Set up new worktree` Zed task with the `create_worktree` hook
(Zed-created worktrees). It creates:

```text
<new-worktree>/.zed/tasks.json -> <ROOT>/.zed/tasks.json
<new-worktree>/.agents-main    -> <ROOT>/ayon-agentic-instructions
```

and copies `.env` from the repo's main checkout.

The previous whole-directory `.zed -> <ROOT>/.zed` symlink is detected and
migrated to the tasks.json-only linkage by `ayon-sdd link` and
`ayon-sdd worktree-setup`; `ayon-sdd status` reports any drift.

## Git checkout resolution

Scripts that receive `$ZED_FILE` must determine which AYON checkout the file
actually belongs to — a direct checkout or a worktree. The shared resolver
lives in `src/jeza_ynput_dev_workspace/repo_context.py` and uses git:

```bash
git -C <file-directory> rev-parse --show-toplevel   # actual checkout root
git -C <file-directory> rev-parse --git-common-dir  # repository identity
```

For example, both of these resolve to `addon: ayon-nuke`:

```text
<ROOT>/worktrees/ayon-nuke/sedge-owl/ayon-nuke/create_package.py
<ROOT>/ayon-nuke/create_package.py
```

The same resolver is reused by `upload-to-addon-folder`,
`create-addon-package` and `git-commit-info-extraction` (previously each had
its own copy of the first-path-component logic).

## Scripts

All entry points are declared in `pyproject.toml` under `[project.scripts]`
and run through `uv run --project <workspace-root>`:

| Script                          | Purpose                                             |
|---------------------------------|-----------------------------------------------------|
| `git-clone-all-repos`           | Clone the full YNPUT repo list                      |
| `upload-to-addon-folder`        | Package + upload addon, restart server              |
| `create-addon-package`          | Run the selected checkout's `create_package.py`     |
| `update-ayon-docker-local-dir`  | Docker compose pull/up for the server               |
| `docs-initialize` / `docs-start`| Docusaurus setup / serve for ayon-documentation     |
| `git-commit-info-extraction`    | Markdown commit history of the selected branch      |
| `launcher-dev-mode`             | Launch AYON launcher in dev mode                    |
| `ayon-launch-app`               | Launch AYON addon apps (menu-driven)                |
| `ayon-sdd <subcommand>`         | Workspace tooling umbrella (see below)              |

Scripts avoid process-wide `os.chdir()`; subprocesses receive an explicit
`cwd` (e.g. the resolved `ayon-docker` directory, the docs `website/`
directory, or the resolved addon checkout).

## `ayon-sdd` subcommands

- `link` / `unlink` — wire/unwire a repo into the shared layer (hooks path,
  `.agents-main`, `.zed/tasks.json`, shared skills).
- `status` — report linkage drift per repo (read-only).
- `worktree-setup` — wire a freshly created worktree (hook + Zed task).
- `install-global` — installs global *agent* instructions
  (`~/.config/zed/AGENTS.md`, `~/.config/goose/AGENTS.md`) and shared
  skills. It deliberately does **not** manage Zed tasks.
- `init-speckit` — install Spec Kit for the in-scope repos.
- `doctor` — regression checks for the whole setup (including that
  `<ROOT>/.zed/tasks.json` parses).
- `bootstrap` — bring a brand-new workspace root to the full state.

## Bootstrapping a new workspace

```bash
git clone https://github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace.git <NEW_ROOT>
cd <NEW_ROOT>
uv sync
uv run ayon-sdd bootstrap --root "$PWD" --dry-run    # review the plan first
uv run ayon-sdd bootstrap --root "$PWD"               # then run it for real
uv run ayon-sdd doctor                                # verify — must exit 0
```

`bootstrap` sequences preflight → clone repos → install global agent
instructions/skills → clone central repo → link repos → init Spec Kit →
doctor. Every step is idempotent.

Because tasks are workspace-local, an unrelated folder opened in Zed does
**not** receive the AYON tasks automatically — that is the intended
trade-off. A new workspace root must be initialized with the tooling above;
once any workspace exists, the `AYON / Bootstrap agentic workspace HERE`
task covers subsequent new folders.

## Verifying

`uv run ayon-sdd doctor` asserts every cheaply-testable invariant
(workspace task file parses, global AGENTS.md files, central repo present,
L2 linkage clean per repo, shared skills regression) and prints a per-check
report:

```text
DOCTOR: OK — every check passed.
```

On failure it prints `DOCTOR: FAIL` followed by one `- ` bullet per problem
and exits 1.

## Environment

Dependencies are managed with `uv` (`pip install uv` first). Tasks install
dependencies automatically when needed. `.env` files with `AYON_SERVER_URL`
and `AYON_API_KEY` are required for server-related tasks.
