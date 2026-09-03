# Jeza Ynput Dev Workspace

This workspace provides a streamlined developmen for YNPUT and ZED projects. It combines essential tools and automated tasks in ZED editor, allowing you to manage multiple repositories efficiently while focusing on creation rather than setup. The integrated environment simplifies your development workflow with centralized commands and tools.

This repository (`jakubjezek001/Jeza-Ynput-Dev-Workspace`) **is** the reproducible
workspace tooling: cloning it and running one command below brings a brand-new,
empty folder to the same multi-repo, agent-aware state as this machine — see
`IMPLEMENTATION-PLAN.md` for the full design (§3 `LW` layer, Phase G).

## Bootstrapping a new workspace from scratch

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) — Python dependency management and script runner.
- `git`.
- [`goose`](https://block.github.io/goose/) — required for the agent-delegation
  workflow; its config must have `GOOSE_MODE: auto` set in
  `~/.config/goose/config.yaml` (§6 D3) — `ayon-sdd doctor`/`bootstrap` verify this,
  they never write it for you.
- [Zed](https://zed.dev/) — the editor the global tasks (below) are written for.

`git` and `uv` are hard requirements (bootstrap refuses to run without them); `zed`
and `goose` are soft — their absence only produces a warning, since the L0
(user-global) layer can still be written without them.

### 1. Clone, sync, bootstrap (the G0(a) chain)

```bash
git clone https://github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace.git <NEW_ROOT>
cd <NEW_ROOT>
uv sync
uv run ayon-sdd bootstrap --root "$PWD" --dry-run    # review the plan first
uv run ayon-sdd bootstrap --root "$PWD"               # then run it for real
uv run ayon-sdd doctor                                # verify — must exit 0
```

There is no chicken-and-egg problem here: cloning this repo alone brings
`.zed/`, `src/` and `pyproject.toml`, so `uv sync` can install the
`[project.scripts]` entry points (including `ayon-sdd`) before anything else
needs to exist. `ayon-sdd bootstrap` then does the rest — the L0 user-global
layer (Phase A), cloning the in-scope repos, the L1 central repo
(`ayon-agentic-instructions`), the L2 per-repo linkage (Phase D), and Spec Kit
installation for the seven §6 D1 repos — finishing with an `ayon-sdd doctor`
report. Every step is idempotent; re-running `bootstrap` is always safe.

**Standalone one-shot scripts were considered and rejected** (§6 D5) — the
two-step chain above (`git clone && uv sync && uv run ayon-sdd bootstrap`) is
the only supported bootstrap path. Do not look for (or build) a PEP 723
one-shot alternative.

### 2. Default scope vs. `--all`

By default, `ayon-sdd bootstrap` clones the **in-scope ten**: the seven §6 D1
repos (`ayon-batch-delivery`, `ayon-flame`, `ayon-resolve`, `ayon-hiero`,
`ayon-core`, `ayon-launcher`, `ayon-nuke`) plus the three permanently
out-of-scope repos needed on disk as read-only local infra
(`ayon-backend`, `ayon-frontend`, `ayon-docker` — never linked or written to).

Pass `--all` to instead clone the full ~40-repo AYON set (the same list
`git-clone-all-repos` already uses):

```bash
uv run ayon-sdd bootstrap --root "$PWD" --all
```

Use `--skip-clone` to run the rest of bootstrap (L0/L1/L2/Spec Kit/doctor)
against repos you already have on disk, without touching git clones at all.

### 3. Zed tasks (from the global `tasks.json`, Phase A1)

`ayon-sdd install-global` (which `bootstrap` calls for you) renders
`~/.config/zed/tasks.json` — a **global** Zed tasks file, so these two tasks
show up in the command palette (`tasks: spawn`) from **any** project opened
in Zed, not just this workspace:

- **`AYON / Bootstrap agentic workspace HERE`** — runs
  `ayon-sdd bootstrap --root $ZED_WORKTREE_ROOT` against whatever folder is
  currently open, using this workspace's `pyproject.toml` to resolve `uv run`.
- **`AYON / Doctor`** — runs `ayon-sdd doctor` for a one-keystroke health check.

### 4. Verifying with `ayon-sdd doctor`

`doctor` is the regression suite for the whole plan — it asserts every
cheaply-testable invariant (global tasks/AGENTS.md files present and valid,
the central repo present, each in-scope repo's L2 linkage clean, the shared
`goose skills list` regression test) and prints a per-check report:

```
DOCTOR: OK — every check passed.
```

On failure it prints `DOCTOR: FAIL` followed by a `- ` bullet per problem and
exits `1` — read each bullet, it names the exact file/repo/config at fault.

### 5. Fresh-machine limitation

The very first workspace on a brand-new machine has no *existing* Zed project
to borrow a `cwd` from, so it must be bootstrapped from a terminal using the
chain in step 1. Once **any** workspace exists, `AYON / Bootstrap agentic
workspace HERE` (step 3) covers every subsequent new folder — its `cwd`
points at this workspace so `uv run` can resolve `pyproject.toml`, while
`--root $ZED_WORKTREE_ROOT` targets the new folder being opened.

## Features and Benefits

This workspace offers several key features to enhance your development experience:

- Built-in commands for cloning essential YNPUT repositories
- Simplified addon packaging and upload process
- Dependency management using UV package installer

## Environment Setup

The workspace uses UV for Python dependency management. To set up your environment:

```bash
pip install uv
```

After installing UV, you should be able just simply run the tasks from the command palette. Dependencies will be installed automatically when needed.

# Features and Usage

## Available Tasks

The workspace includes several pre-configured tasks that can be executed through ZED's command palette. To run any task:

1. Open the command palette (Cmd/Ctrl + Shift + P)
2. Type `tasks: spawn`
3. Select the desired task from the list

### Available Tasks:

#### 1. Git Clone all repositories
**Purpose:** Clones all essential YNPUT repositories to your local workspace.
**Usage:**
- Select "Git Clone all repositories" from the tasks menu
- The task will execute in the current terminal
- Repositories will be cloned to your workspace directory

#### 2. Upload addon to server and restart
**Purpose:** Uploads the current file to the addon folder and restarts the service.
**Usage:**
- Active file must be an addon-related file
- Select "Upload addon to server and restart" from the tasks menu
- Supports debug mode with the `--debug` flag (enabled by default)
- Task will execute in the current terminal
- Terminal will auto-hide on successful completion
**Requirements:**
- Server has to have at least one service user so AYON_API_KEY can be used
- .env file with `AYON_API_KEY` and `AYON_SERVER_URL` variables

#### 3. Update AYON server
**Purpose:** Updates the AYON server using Docker Compose.
**Usage:**
- Select "Update AYON server" from the tasks menu
- Task will:
  1. Change directory to `ayon-docker`
  2. Pull the latest server image
  3. Restart the server container
- Executes in a new terminal window
- Terminal will auto-hide on successful completion

#### 4. Initialize Docs
**Purpose:** Initializes the documentation environment and dependencies.
**Usage:**
- Select "Initialize Docs" from the tasks menu
- Task will instlal `yarn` if not already installed
- Task will set up the necessary documentation structure and install all required Docusaurus dependencies
- Uses system shell for execution
- Terminal will auto-hide on successful completion

#### 5. Start Docs
**Purpose:** Starts the documentation server for live preview and editing.
**Usage:**
- Select "Start Docs" from the tasks menu
- Launches in a new terminal window
- Allows concurrent runs with other tasks
- Terminal remains visible for monitoring
- Documentation server will stay active for real-time preview

## Task Execution Behavior

All tasks are configured with the following common behaviors:
- Concurrent runs are not allowed (tasks will wait for previous instances to complete)
- Task output is visible in the terminal
- Summary and command output are shown by default
- Tasks use the system's default shell configuration

> [!TIP]
> Tasks with `hide: "on_success"` will automatically hide the terminal tab when completed successfully, keeping your workspace clean and organized.

> [!NOTE]
> Some features may require initial setup and configuration of your development environment.
