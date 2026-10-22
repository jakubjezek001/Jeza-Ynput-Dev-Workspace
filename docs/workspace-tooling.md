# Workspace tooling

All tooling lives in `src/jeza_ynput_dev_workspace/` and is exposed as
`[project.scripts]` entry points in `pyproject.toml`. Run every command from
the workspace root with `uv run <entry-point>`. `uv run` installs the
dependencies on first use. Python is pinned to `>=3.9.19,<3.11`.

## Commands

| Entry point | What it does |
| --- | --- |
| `git-clone-all-repos` | Clone every AYON repository in `git_clone_all_repos.ALL_REPOS` into the current directory; existing folders are skipped |
| `upload-to-addon-folder` | Upload an addon package to the server and restart it (`-f <file in addon>`, `--debug`) |
| `create-addon-package` | Build an addon package and open it in the browser (`-f <file in addon>`) |
| `remove-unused-addons` | Remove `ayon-docker/addons/<addon>/<version>` folders that no active bundle pins; dry run unless `--apply` (see below) |
| `update-ayon-docker-local-dir` | Pull the latest server image in `ayon-docker` and restart the container (run from the workspace root) |
| `docs-initialize`, `docs-start` | Install and serve the Docusaurus docs (`ayon-documentation`) |
| `git-commit-info-extraction` | Print the commit history of the current branch in the repo that contains `-f <file>` |
| `ayon-launch-app` | Run any `ayon-launcher` `start.py` addon command through the launcher venv (e.g. `addon applications launch --project … --folder … --task …`) |
| `launcher-dev-mode` | Start `ayon-launcher` in dev mode |
| `ayon-workspace` | Workspace setup: global Zed tasks, repo/worktree linking, bootstrap (see below) |

The click-based commands accept `--help`. The required `.env` keys are listed in
[workspace.md](workspace.md#environment).

### `remove-unused-addons`

- Without `--apply`, it only lists the folders it would remove and their
  sizes. With `--apply`, it asks `[y/N]`, deletes them, restarts the server
  and checks that the server lists exactly the versions left on disk.
- Run with `--path` inside an addon repo or worktree, it only covers that
  addon (the name comes from its `package.py`). Run from anywhere else, it
  covers every addon. `--addon` names the addon directly.
- Always kept whole: `sn4`, anything passed with `--keep`, and addons that
  an active bundle has an enabled dev path for but pins no version of. An
  addon with no version left is removed as a whole folder.

## Zed tasks

`.zed/tasks.json` holds the workspace tasks: Git clone, upload/package an
addon, remove unused addon versions, update the server, docs, ruff on the
current file, and launching AYON apps. Open them with `tasks: spawn` in the
command palette.

Zed only shows a project's own `.zed/tasks.json`, so these tasks are lost
when a single `ayon-*` repo or a worktree is opened. Two mechanisms bring
them back:

1. **Global tasks:** `uv run ayon-workspace install-global` renders
   `src/jeza_ynput_dev_workspace/templates/zed_tasks.json.tmpl` into
   `~/.config/zed/tasks.json`, which Zed shows in every project. That file
   is generated. Edit the template, never the output, and keep it in sync
   with `.zed/tasks.json` when you add a task. The global set also contains
   `Utils / Set up new worktree` (a `create_worktree` hook),
   `AYON / Bootstrap workspace HERE` and `AYON / Doctor`.
2. **Linked repos:** `ayon-workspace link` symlinks `<repo>/.zed` to the
   workspace `.zed/`, so the repo also gets the workspace settings and
   debug config.

Tasks that need the workspace root use `${AYON_WORKSPACE_ROOT:<root>}`.
Zed silently hides a task whose variable cannot be resolved, so always give
a default.

## `ayon-workspace`

```bash
uv run ayon-workspace install-global [--dry-run]   # write ~/.config/zed/tasks.json
uv run ayon-workspace link   (--repo PATH ... | --all) [--dry-run]
uv run ayon-workspace unlink (--repo PATH ... | --all) [--dry-run]
uv run ayon-workspace status (--repo PATH ... | --all)
uv run ayon-workspace doctor                       # read-only health check
uv run ayon-workspace bootstrap [--root PATH] [--dry-run] [--skip-clone] [--all]
```

- `--all` means the repos in `workspace_common.SCOPE_REPOS`. Any other repo
  can be linked with `--repo`. The server repos (`ayon-backend`,
  `ayon-frontend`, `ayon-docker`) are always refused.
- `link` does three things for each repo: it sets `core.hooksPath` to the
  absolute `<root>/.githooks-shared`, symlinks `.zed` to `../.zed`, and
  hides that symlink in `.git/info/exclude`. Nothing is committed to the
  repo, and a path the repo already tracks is never replaced.
- `worktree-setup` runs automatically for every new linked worktree,
  through the `post-checkout` hook (`git worktree add`) and through the Zed
  `create_worktree` task. It symlinks `.zed` with an absolute target and
  copies `.env` from the main checkout. It never fails a checkout.
- `doctor` checks that the global tasks file parses and that every linked
  repo on disk is clean. It exits 1 on drift.

### Why it is built this way

These git and Zed behaviours were verified and the design depends on them:

- `post-checkout` fires on `git worktree add` with `$1` = 40 zeros and
  `$3` = `1`. A linked worktree is detected by `git rev-parse --git-dir`
  differing from `--git-common-dir`.
- An absolute `core.hooksPath` outside the repo also fires in new
  worktrees, with nothing committed.
- `git worktree add` never copies untracked or ignored files (`.env`,
  symlinks). That is why `worktree-setup` exists.
- `.git/info/exclude` lives in the common git dir and is shared by every
  worktree. A symlink to a directory must be listed without a trailing
  slash (`/.zed`, not `/.zed/`), or git does not ignore it.
- Zed has no project-open hook, startup script or `.zed-workspace` file.
  The only hook is the `create_worktree` task hook, which gets
  `$ZED_WORKTREE_ROOT` and `$ZED_MAIN_GIT_WORKTREE`. A multi-root window
  does not union the tasks of its roots. A symlinked `.zed/` is read.
- A task's `cwd` may point outside the project, which lets a global task
  run `uv run` against the workspace `pyproject.toml`.

## Bootstrapping a new workspace

Prerequisites: `git` and `uv` (required), Zed (optional).

```bash
git clone https://github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace.git <NEW_ROOT>
cd <NEW_ROOT>
uv sync
uv run ayon-workspace bootstrap --root "$PWD" --dry-run   # review the plan
uv run ayon-workspace bootstrap --root "$PWD"
```

Bootstrap clones the repos in `SCOPE_REPOS` plus the read-only server repos
(`--all` clones the full `ALL_REPOS` list, `--skip-clone` clones nothing).
It then installs the global Zed tasks, links the repos, and finishes with
`doctor`. Every step is idempotent, so re-running it is safe. Once one
workspace exists, the global `AYON / Bootstrap workspace HERE` task
bootstraps any folder open in Zed.
