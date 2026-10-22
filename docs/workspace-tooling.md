# Workspace tooling

All tooling lives in `src/jeza_ynput_dev_workspace/` and is exposed as
`[project.scripts]` entry points in `pyproject.toml`. Run them with
`uv run <entry-point>` from the workspace root, or from anywhere with
`uv run --project <root> <entry-point>`. `uv run` installs the dependencies
on first use. Python is pinned to `>=3.9.19,<3.11`.

## Commands

| Entry point | What it does |
| --- | --- |
| `git-clone-all-repos` | Clone every AYON repository in `git_clone_all_repos.ALL_REPOS` into the workspace root; existing folders are skipped |
| `upload-to-addon-folder` | Package the checkout that contains `-f <file>`, upload it, restart the server, then update the development bundle (`--bundle`, defaults to `AYON_STUDIO_BUNDLE_NAME`; `--no-bundle-update`, `--force-bundle`) |
| `create-addon-package` | Run `create_package.py` of the checkout that contains `-f <file>` and open its `package/` folder |
| `remove-unused-addons` | Remove `ayon-docker/addons/<addon>/<version>` folders that no active bundle pins; dry run unless `--apply` (see below) |
| `update-ayon-docker-local-dir` | Pull the latest server image in `ayon-docker` and restart the container |
| `docs-initialize`, `docs-start` | Install and serve the Docusaurus docs (`ayon-documentation`) |
| `git-commit-info-extraction` | Print the commit history of the current branch in the repo that contains `-f <file>` |
| `ayon-launch-app` | Run any `ayon-launcher` `start.py` addon command through the launcher venv (e.g. `addon applications launch --project … --folder … --task …`) |
| `launcher-dev-mode` | Start `ayon-launcher` in dev mode |
| `ayon-workspace` | Workspace setup: Zed task linking for repos and worktrees, bootstrap (see below) |

The click-based commands accept `--help`. The required `.env` keys are listed in
[workspace.md](workspace.md#environment).

Commands that take `-f <file>` find the checkout with git
(`repo_context.resolve_checkout`: `git rev-parse --show-toplevel` and
`--git-common-dir`), so a file in `ayon-nuke/` and the same file in
`worktrees/ayon-nuke/<name>/ayon-nuke/` both resolve to `ayon-nuke`, each
in its own checkout. Scripts never `chdir`; they pass `cwd` to
subprocesses.

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

`<root>/.zed/tasks.json` is the single, canonical task file: Git clone,
upload/package an addon, remove unused addon versions, update the server,
docs, ruff on the current file, launching AYON apps, plus
`Utils / Set up new worktree` (a `create_worktree` hook),
`AYON / Bootstrap workspace` and `AYON / Doctor`. Open them with
`tasks: spawn` in the command palette.

Zed only shows the open project's own `.zed/tasks.json`, so every linked
repo and worktree gets a symlink to the canonical file:

```text
ayon-core/.zed/tasks.json -> ../../.zed/tasks.json
worktrees/ayon-nuke/<name>/ayon-nuke/.zed/tasks.json -> <root>/.zed/tasks.json
```

Only `tasks.json` is linked; a repo's own `.zed/settings.json` and
`.zed/debug.json` are kept. A folder that is not linked gets no tasks; that
is the intended trade-off. There is no global `~/.config/zed/tasks.json`.

How the tasks are written:

- Every task runs `uv run --project ${AYON_WORKSPACE_ROOT} <entry-point>`,
  so `uv` never picks up `ayon-core`'s, `ayon-launcher`'s or an addon's own
  `pyproject.toml`.
- Workspace tasks run with `cwd` = `${AYON_WORKSPACE_ROOT}` (they need the
  workspace `.env`, `ayon-docker`, `ayon-launcher`). Tasks about the open
  repo (ruff, git commit info, remove unused addon versions) run with
  `cwd` = `$ZED_WORKTREE_ROOT`, so that repo's ruff config and git metadata
  apply.
- File tasks pass `$ZED_FILE` (absolute); the scripts resolve its checkout.
- When you add a task, add it to `<root>/.zed/tasks.json` only.

`AYON_WORKSPACE_ROOT` must be set in the environment Zed starts with: Zed
expands it in `cwd`, the shell expands it in `args`. Export it from your
shell profile (for example `export AYON_WORKSPACE_ROOT=<root>` in
`~/.zshenv`), or set it under `terminal.env` in Zed's settings, then quit
and reopen Zed. Without it, `cwd` falls back to `/` and the tasks fail.

## `ayon-workspace`

```bash
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
  absolute `<root>/.githooks-shared`, symlinks `.zed/tasks.json` to
  `../../.zed/tasks.json` (creating `.zed/` if needed), and hides that
  symlink in `.git/info/exclude`. Nothing is committed to the repo, and a
  path the repo already tracks is never replaced. An old whole-directory
  `.zed -> <root>/.zed` link is replaced by the file link.
- `worktree-setup` runs automatically for every new linked worktree,
  through the `post-checkout` hook (`git worktree add`) and through the
  `Utils / Set up new worktree` Zed task (`create_worktree` hook). It links
  `.zed/tasks.json` with an absolute target and copies `.env` and
  `service_tools/.env` from the main checkout. It never fails a checkout.
- `doctor` checks that `<root>/.zed/tasks.json` parses and that every
  linked repo on disk is clean. It exits 1 on drift.

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
  worktree. Symlink entries are listed without a trailing slash
  (`/.zed/tasks.json`).
- Zed has no project-open hook, startup script or `.zed-workspace` file.
  The only hook is the `create_worktree` task hook, which gets
  `$ZED_WORKTREE_ROOT` and `$ZED_MAIN_GIT_WORKTREE`. A multi-root window
  does not union the tasks of its roots.
- A task's `cwd` may point outside the project, which lets a linked task
  run against the workspace root.

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
(`--all` clones the full `ALL_REPOS` list, `--skip-clone` clones nothing),
links the repos, and finishes with `doctor`. Every step is idempotent, so
re-running it is safe. Then set `AYON_WORKSPACE_ROOT` for Zed (see
[Zed tasks](#zed-tasks)).
