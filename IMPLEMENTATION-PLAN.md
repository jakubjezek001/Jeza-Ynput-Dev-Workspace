# Implementation plan — workspace-local Zed tasks architecture

Status: **implemented**. This document replaces the previous
`IMPLEMENTATION-PLAN.md` (which described a global
`~/.config/zed/tasks.json` layer and whole-directory `.zed` symlinks). The
old global-task implementation has been removed.

## Architecture

1. **One canonical task file**: `<ROOT>/.zed/tasks.json` (16 tasks, strict
   JSON) is the single source of Zed tasks. No `~/.config/zed/tasks.json`
   is created or managed (`~/.config/zed/___tasks.json` may remain as a
   manual backup but does not participate in discovery).

2. **tasks.json-only linkage**: repositories and worktrees symlink only
   `.zed/tasks.json`:

   ```text
   repo/.zed/tasks.json    -> ../.zed/tasks.json          (direct checkout)
   worktree/.zed/tasks.json -> <ROOT>/.zed/tasks.json      (worktree)
   ```

   Repository-owned `.zed/settings.json` / `.zed/debug.json` are never
   replaced. The previous `.zed -> <ROOT>/.zed` directory symlink is
   migrated automatically by `ayon-sdd link` and `ayon-sdd worktree-setup`.

3. **Explicit `uv --project`**: every workspace-owned command runs
   `uv run --project <ROOT> <script>` so `uv` never selects an addon's
   `pyproject.toml`. The `args` carry the literal root path: Zed expands
   `${VAR:default}` in `cwd` but not in `args`, and zsh would otherwise
   expand the unset `AYON_WORKSPACE_ROOT` to an empty string, making `uv`
   swallow the script name as the project and fail on the script's own
   flags (e.g. `-f` collides with `uv run --find-links`, `--debug` is
   unexpected). `cwd` keeps the `${AYON_WORKSPACE_ROOT:<ROOT>}` form, which
   Zed expands and which stays overridable via the environment variable.

4. **Selected-file resolution**: file-based tasks pass `$ZED_FILE`
   (absolute). `repo_context.resolve_checkout()` uses
   `git rev-parse --show-toplevel` / `--git-common-dir` to find the real
   checkout (main or worktree); shared by upload, package creation and
   commit-info commands.

5. **Working-directory policy**: workspace tasks run from
   `${AYON_WORKSPACE_ROOT:...}`; selected-repository tasks (Ruff, git
   commit info) run from `$ZED_WORKTREE_ROOT`.

6. **Worktree callback**: `Utils / Set up new worktree` (with the
   `create_worktree` hook) and the shared `post-checkout` git hook both call
   the same `ayon-sdd worktree-setup` implementation.

## Files

- `.zed/tasks.json` — canonical 16-task file (Option A: default workspace
  root baked in, overridable via `AYON_WORKSPACE_ROOT`).
- `src/jeza_ynput_dev_workspace/repo_context.py` — shared Git checkout
  resolver (`CheckoutContext`).
- `src/jeza_ynput_dev_workspace/sdd_link.py` — tasks.json-only linkage +
  legacy `.zed` symlink migration.
- `src/jeza_ynput_dev_workspace/sdd_worktree_setup.py` — worktree linkage
  (tasks.json + `.agents-main` + `.env`) + legacy migration.
- `src/jeza_ynput_dev_workspace/sdd_install_global.py` — agent
  instructions/skills only; Zed tasks no longer managed.
- `src/jeza_ynput_dev_workspace/sdd_doctor.py` — checks
  `<ROOT>/.zed/tasks.json` instead of the global file.
- `src/jeza_ynput_dev_workspace/{upload_to_addon_folder,create_addon_package,git_commit_info_extraction}.py`
  — use the shared resolver.
- `src/jeza_ynput_dev_workspace/{update_ayon_docker_local_dir,docs_initialize,docs_start}.py`
  — explicit subprocess `cwd`, no process-wide `os.chdir`.

## Acceptance

- [ ] `uv run ayon-sdd doctor` exits 0.
- [ ] `.zed/tasks.json` is valid strict JSON with all 16 tasks and
      `--project` on every workspace command.
- [ ] `ayon-sdd link --all` + `ayon-sdd worktree-setup` produce
      tasks.json-only symlinks and migrate legacy `.zed` links.
- [ ] `~/.config/zed/tasks.json` is absent; no duplicate tasks appear.
