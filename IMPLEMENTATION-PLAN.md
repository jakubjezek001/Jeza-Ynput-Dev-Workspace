# AYON SDD Workflow — Implementation Plan

> **Audience:** the **goose** agent executing Phase 2 (Implementation).
> **Status:** Output of Phase 1 (Research & Design). No code was written in Phase 1.
> **Research date:** 2026-09-02. Versions probed on this workstation: **Zed 1.17.2**, **goose 1.47.0**.

---

## 0. How to use this document

You are implementing a Spec-Driven Development (SDD) workflow across a multi-repository
AYON workspace. This document is your specification.

**Rules for you, the implementing agent:**

1. Work through the phases in order. **Do not** start Phase B before Phase A is verified.
2. Every task has an ID (`A1`, `B2`, …), an explicit **Acceptance test** and a
   **Verify** command. A task is done only when its Verify command passes.
3. Record all tasks in your todo list before touching anything.
4. **Do not invent mechanisms.** §2 lists what is verified to work and what is
   verified *not* to work. If a task seems to need an unlisted mechanism, stop and
   report instead of improvising.
5. Anything marked **⚠ VERIFY FIRST** is code-verified but not runtime-verified.
   Run the stated experiment before building on it. If it fails, use the stated fallback.
6. Never modify: `__TESTs/`, `.venv`, `*.worktrees/`, `worktrees/`, `.env*`, `uv.*`,
   or any `ayon-*` folder not listed in §1.
7. Never commit to `ayon-backend`, `ayon-frontend`, `ayon-docker`.

---

## 1. Scope

**Workspace root** (`<ROOT>`): `/Users/jakub/CODE/__YNPUT` — a personal, unpublished wrapper.

| Repo | Role in this plan |
| --- | --- |
| `ayon-agentic-instructions` | **Single source of truth** for shared SDD content. Remote: `github.com/ynput/ayon-agentic-instructions` |
| `ayon-core`, `ayon-launcher` | Client repos — receive SDD instructions, read-mostly |
| `ayon-batch-delivery`, `ayon-nuke`, `ayon-flame`, `ayon-resolve`, `ayon-hiero` | Addon repos — receive SDD + addon-specific instructions |
| `ayon-backend`, `ayon-frontend`, `ayon-docker` | **Do not touch** |

Everything else under `<ROOT>` is out of scope.

### 1.1 Current state (surveyed 2026-09-02)

```
<ROOT>/.zed/{tasks.json,settings.json,debug.json,launch_subprocess.py}
<ROOT>/src/jeza_ynput_dev_workspace/*.py   # uv entry points used by .zed/tasks.json
<ROOT>/pyproject.toml                       # [project.scripts] -> the task commands
<ROOT>/.agents/skills/{harsh-code-review,yn-pr-description,yn-pr-update}/SKILL.md
<ROOT>/.agents/agents/                      # empty

ayon-agentic-instructions/
  AGENTS.md                 # generic AYON addon instructions (already good)
  CLAUDE.md -> AGENTS.md    # committed symlink
  .kilo -> .agents          # committed symlink
  .agents/agents/{explorer.md,reviewer.md}
  .agents/skills/{harsh-code-review,yn-pr-description,yn-pr-update}/SKILL.md
  .claude/skills -> ../.agents/skills

ayon-nuke/                  # the existing prototype
  AGENTS.md                 # nuke-specific, references ".agents-main/AGENTS.md
  .agents-main -> ../ayon-agentic-instructions   # local symlink
  .githooks/post-checkout   # clones the central repo into new worktrees
  core.hooksPath = .githooks
  .zed/                     # EMPTY

ayon-batch-delivery/
  .agents-main -> ../ayon-agentic-instructions
  .github/copilot-instructions.md
  .zed/settings.json
  (no AGENTS.md, no hooks)

ayon-flame, ayon-resolve, ayon-hiero, ayon-core, ayon-launcher: no agentic files at all
```

**Known defects in the current prototype (fix them, don't preserve them):**

- The `post-checkout` hook `git clone`s the central repo into every new worktree.
  That is a network round-trip and an immediately-stale copy. Replace with a symlink
  to the single local checkout.
- `core.hooksPath = .githooks` is **relative**, so the hook only exists in a worktree
  if `.githooks/` is committed. Use an absolute shared path instead (verified in §2.1).
- `ayon-nuke/.zed/` is an empty directory doing nothing.

---

## 2. Verified research baseline

Two confidence levels are used:
**[EMPIRICAL]** = I ran it on this machine on 2026-09-02.
**[SOURCE]** = read from the tool's source/docs at HEAD.

### 2.1 Git — the distribution substrate

| # | Fact | Confidence |
| --- | --- | --- |
| G1 | `post-checkout` **does** fire on `git worktree add`, with `$1` = 40 zeros, `$2` = new HEAD, `$3` = `1`. Inside the hook `git rev-parse --git-dir` != `--git-common-dir`, which is the reliable "this is a linked worktree" test. | **[EMPIRICAL]** |
| G2 | `core.hooksPath` set to an **absolute path outside the repo** fires correctly in newly created worktrees, with **nothing committed** to the repo. | **[EMPIRICAL]** |
| G3 | `git worktree add` does **not** copy untracked or gitignored files (`.env`, untracked files, symlinks) into the new worktree. | **[EMPIRICAL]** |
| G4 | `.git/info/exclude` lives in the **common** git dir and is **shared by every linked worktree**. `git check-ignore -v` inside a worktree resolves to `<main>/.git/info/exclude`. This lets you hide local symlinks **without editing any repo's committed `.gitignore`**. | **[EMPIRICAL]** |
| G5 | In `.git/info/exclude`, a symlink-to-directory must be listed **without a trailing slash** (`/.agents-main`, not `/.agents-main/`). With a trailing slash it is not ignored — git sees a symlink, not a directory. | **[EMPIRICAL]** |

> **G4 + G2 are the backbone of this design:** shared config reaches every repo and
> every worktree with **zero commits** to the AYON repos.

### 2.2 Goose (1.47.0)

| # | Fact | Confidence |
| --- | --- | --- |
| N1 | **The workspace-root `.agents/skills` is invisible from inside a child repo.** `goose skills list` from `<ROOT>` lists the 3 root skills; from `<ROOT>/ayon-nuke` it lists **none** of them. This is exactly the limitation stated in `PLAN.md`. | **[EMPIRICAL]** |
| N2 | `~/.agents/skills/` **is** visible from every directory. | **[EMPIRICAL]** |
| N3 | Goose resolves **both** a symlinked `.agents/skills` directory **and** a symlinked individual `.agents/skills/<name>` folder. | **[EMPIRICAL]** |
| N4 | Hint files are `.goosehints` and `AGENTS.md` only (there is no `.goosehints.md`). Both are loaded. Configurable via `CONTEXT_FILE_NAMES` (**filenames, not paths**). | **[SOURCE]** `crates/goose/src/hints/load_hints.rs:10-24` |
| N5 | Local hint discovery walks **up from cwd and stops at the git root**. `@`-imports are clamped to the same boundary, so `@../shared/x.md` will **not** resolve out of a repo. Same root cause as N1. | **[SOURCE]** `load_hints.rs:170-209,265` |
| N6 | Global hints: `~/.config/goose/AGENTS.md`, `~/.config/goose/.goosehints`, and `~/.agents/AGENTS.md`. | **[SOURCE]** `load_hints.rs:239-248` |
| N7 | Recipe discovery order: cwd → `GOOSE_RECIPE_PATH` (colon-separated) → `~/.config/goose/recipes/` → `./.goose/recipes/` → `GOOSE_RECIPE_GITHUB_REPO`. | **[SOURCE]** docs `storing-recipes` |
| N8 | Recipes support `sub_recipes`, per-recipe `settings.goose_provider` / `goose_model`, `parameters`, `response.json_schema`, `retry.checks`, and Jinja templating with a built-in `{{ recipe_dir }}`. | **[SOURCE]** docs `recipe-reference` |
| N9 | **`GOOSE_LEAD_MODEL` / lead-worker no longer exists.** The supported way to run a small local model for a subtask is **per-recipe `settings.goose_provider`** (plus `GOOSE_FAST_MODEL` for auxiliary calls, `GOOSE_PLANNER_MODEL` for `/plan`). | **[SOURCE]** 0 hits in source & docs at HEAD |
| N10 | **Subagents are disabled unless `GOOSE_MODE=auto`.** The user currently runs `smart_approve`, so delegation silently does nothing. | **[SOURCE]** docs `subagents` |
| N11 | Goose has **no** built-in embeddings / vector store / RAG. The `memory` extension is plain files injected wholesale into every prompt — it does not scale. Structural search is provided by the `analyze` (tree-sitter) extension. | **[SOURCE]** no embedding/vector code in `crates/` |
| N12 | `goose review` discovers checks from `.agents/checks/*.md` and scoped instructions from `.agents/REVIEW.md`. Useful as an SDD verify gate. | **[SOURCE]** CLI docs |
| N13 | There is **no official goose GitHub Action**. The documented CI pattern installs the CLI in a step and requires `keyring: false`. | **[SOURCE]** repo has no `action.yml` |
| N14 | Non-interactive: `goose run --recipe X --params k=v --no-session -q --output-format json --max-turns N`. | **[EMPIRICAL]** `goose run --help` |

### 2.3 Zed (1.17.2)

| # | Fact | Confidence |
| --- | --- | --- |
| Z1 | **Global `~/.config/zed/tasks.json` tasks appear in every project.** This alone solves "I lose my Zed tasks when I open a single repo". | **[SOURCE]** docs `tasks` + `task_inventory.rs:439,472` |
| Z2 | **`~/.config/zed/AGENTS.md` is loaded as personal agent instructions in every project.** | **[SOURCE]** `paths.rs:319-320`, docs `ai/instructions` |
| Z3 | Skills live in `~/.agents/skills/` (global, every project) and `<worktree>/.agents/skills/` (project). Docs explicitly bless symlinks: *"Use a symlink if you need to point at another location."* | **[SOURCE]** docs `ai/skills` |
| Z4 | Project instruction file precedence, **first match wins, worktree root only, no subdirectory search**: `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`. | **[SOURCE]** `prompt_store/src/prompts.rs:22-32` |
| Z5 | **There is no project-open hook, no startup script, no extension activation event.** The *only* hook is the `create_worktree` task hook. Feature request #8325 open since 2024. | **[SOURCE]** `TaskHook` enum has exactly one variant |
| Z6 | `"hooks": ["create_worktree"]` tasks run after Zed creates a linked worktree, with `$ZED_WORKTREE_ROOT` = new worktree and `$ZED_MAIN_GIT_WORKTREE` = original repo. The user **already uses this** in `<ROOT>/.zed/tasks.json`. | **[SOURCE]** docs `tasks` + existing config |
| Z7 | Task `cwd` is an unvalidated `Option<String>` — it **may point outside the worktree**. Combined with `${VAR:default}` this lets a global task reach `<ROOT>`. | **[SOURCE]** `task_template.rs:35-37` |
| Z8 | Tasks with an **unresolvable** variable are silently filtered out of the modal. Always use `${VAR:default}`. | **[SOURCE]** docs `tasks` |
| Z9 | Multi-root projects exist (`zed a b`, `--add`), **but the task modal is scoped to the *active* worktree**. Opening `<ROOT>` + `ayon-nuke` together does **not** union their tasks. Multi-root is also currently buggy with git worktrees (#58302, #62331 open). | **[SOURCE]** `task_inventory.rs:432-443` |
| Z10 | **`agent_servers` (ACP agents, incl. goose) is user-settings only** — it cannot be set per-repo in `.zed/settings.json`. | **[SOURCE]** on `SettingsContent`, not `ProjectSettingsContent` |
| Z11 | **`context_servers` (MCP) *can* be set per-repo** in `.zed/settings.json`. Gated on worktree trust. | **[SOURCE]** `project.rs:70` |
| Z12 | `.zed/` directories are **force-scanned** even when external/symlinked/ignored — the check is an unconditional `||` after the `is_external` test. So a symlinked `.zed` should work. **⚠ VERIFY FIRST** (code-verified, not runtime-verified). | **[SOURCE]** `worktree.rs:6217-6241` |
| Z13 | There is **no `.zed-workspace` / `.code-workspace` support** (#9459 open, PR #46225 unmerged). | **[SOURCE]** |
| Z14 | Symlinked config JSON breaks JSON schema autocomplete (#54888 open). Cosmetic but annoying. | **[SOURCE]** |

### 2.4 GitHub Spec Kit — adopt, do not reinvent

`github/spec-kit` at HEAD ships first-class integrations for **all four** of the user's agents.

| # | Fact | Confidence |
| --- | --- | --- |
| S1 | Registered integrations include `goose`, `zed`, `copilot`, `kilocode`, `claude` (35+ total). | **[SOURCE]** `src/specify_cli/integrations/__init__.py` |
| S2 | Running `specify init . --here --force --non-interactive --integration <a> --ignore-agent-tools` **four times** (goose, zed, copilot, kilocode) in one directory succeeds and produces four coexisting command sets over **one shared `.specify/`**. | **[EMPIRICAL]** |
| S3 | Install targets: `goose` → `.goose/recipes/speckit.<n>.yaml`; `zed` → `.agents/skills/speckit-<n>/SKILL.md`; `copilot` → `.github/skills/speckit-<n>/SKILL.md`; `kilocode` → `.kilo/commands/speckit.<n>.md`. | **[EMPIRICAL]** |
| S4 | **The Zed target `.agents/skills/` is the same directory Goose reads.** After installing the zed integration, `goose skills list` showed all 10 `speckit-*` skills, and `goose recipe list` showed all 10 recipes. One install, two agents. | **[EMPIRICAL]** |
| S5 | Generated layout: `.specify/{memory/constitution.md, scripts/bash/{check-prerequisites,common,create-new-feature,resolve-template,setup-plan,setup-tasks}.sh, templates/{spec,plan,tasks,checklist,constitution}-template.md, workflows/, integrations/}`. Feature dirs `specs/NNN-slug/` are created later by `create-new-feature.sh`. | **[EMPIRICAL]** |
| S6 | Commands: `/speckit.constitution`, `.specify`, `.clarify`, `.plan`, `.tasks`, `.analyze`, `.checklist`, `.implement`, `.converge`, `.taskstoissues`. | **[EMPIRICAL]** |
| S7 | Spec Kit is markdown templates + bash scripts + a bundled installer. `specify init` needs no network (assets are bundled). Project-local overrides: `.specify/templates/overrides/` (priority 1), presets (2), extensions (3). | **[SOURCE]** README |
| S8 | Install: `uv tool install specify-cli` (PyPI) or `--from git+https://github.com/github/spec-kit.git@vX.Y.Z`. | **[SOURCE]** README |

**Design consequence:** Spec Kit supplies the *SDD machinery* (specify → clarify → plan →
tasks → analyze → implement → converge). `ayon-agentic-instructions` supplies the
*AYON domain knowledge* (constitution, addon conventions, review checks). Do not
rewrite the former.

### 2.5 Cross-agent instruction standards

| # | Fact | Confidence |
| --- | --- | --- |
| X1 | **`AGENTS.md` is the one file every target agent reads.** Zed (Z4), Goose (N4), Copilot, Kilo, Claude Code. It is the interoperability keystone. | **[SOURCE]** |
| X2 | Copilot **cloud agent** honors: `AGENTS.md` (*anywhere* in the repo, **nearest-in-tree wins**), `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md` (`applyTo` globs). Copilot **Chat on github.com** honors only `.github/copilot-instructions.md`. | **[SOURCE]** docs.github.com `custom-instructions-support` |
| X3 | Copilot precedence: personal → path-specific → repo-wide → agent instructions → org. | **[SOURCE]** |
| X4 | Copilot code review reads instructions/skills from the **head branch** of a PR, so instruction changes can be tested in the same PR. | **[SOURCE]** |
| X5 | Kilo reads `AGENTS.md` natively (incl. per-directory). Rules: `.kilo/rules/` (project, legacy `.kilocode/rules/`), `~/.kilo/rules/` (global). | **[SOURCE]** kilo.ai docs |
| X6 | Zed reads `.github/copilot-instructions.md` **before** `AGENTS.md` (Z4). `ayon-batch-delivery` already has one — it will win over any `AGENTS.md` you add there. Reconcile it. | **[SOURCE]** |

### 2.6 Local inference & retrieval

Available on this workstation (`ollama list`): `nomic-embed-text`, `qwen2.5-coder:3b`,
`ornith:9b`, `ornith-128k`, `qwen3.5:9b`. Goose already has `ollama` configured as a
provider with `ornith:9b`.

| # | Fact | Confidence |
| --- | --- | --- |
| R1 | Goose has no built-in RAG (N11). Any semantic search must come from an **MCP server**. | **[SOURCE]** |
| R2 | Maintained local code-RAG MCP servers: **chunkhound** (`github.com/chunkhound/chunkhound`, Python/`uv tool install chunkhound`, tree-sitter chunking, regex + semantic, Ollama embeddings, SQLite) and **zilliztech/claude-context** (Node, Milvus). The user's `<ROOT>/.gitignore` already ignores `.chunkhound`, so chunkhound has been tried here. | **[SOURCE]** |
| R3 | For "which file implements X" over ~10 Python repos, Goose's built-in **`analyze`** (tree-sitter) extension and `ast-grep`/ripgrep are **cheaper and more accurate** than embeddings. Embeddings help for fuzzy natural-language recall over *prose* (specs, ADRs, docs), not for symbol lookup. | Judgement, flagged as such |

**Recommendation:** treat embeddings as **optional Phase F**, scoped to indexing the
*SDD corpus* (specs/plans/constitution/docs), **not** the Python source. Ship Phases A–E
first; they deliver the whole workflow with zero embedding infrastructure.

### 2.7 Verified dead ends — do not attempt

- ❌ A Zed "open project" hook or startup script (Z5).
- ❌ A `.zed-workspace` file (Z13).
- ❌ A Zed extension that contributes tasks or settings (not in `extension.toml`).
- ❌ Unioning `<ROOT>` + repo tasks via a multi-root window (Z9).
- ❌ Per-repo ACP/goose agent config in `.zed/settings.json` (Z10).
- ❌ A workspace-root `AGENTS.md` or `.agents/` reaching into child repos (N1/N5).
- ❌ `@../outside-repo.md` imports in goose hints (N5).
- ❌ `GOOSE_LEAD_MODEL` (N9).
- ❌ An official goose GitHub Action (N13).

---

## 3. Target architecture

Four layers. Each solves a specific failure mode.

```
L0  USER-GLOBAL          ~/.config/zed/{tasks.json,AGENTS.md}
    (no repo touched)    ~/.config/goose/AGENTS.md
                         ~/.agents/skills/  ~/.agents/agents/
    -> fixes: "I lose Zed tasks and agent context inside a repo"  (Z1,Z2,Z3,N2,N6)

L1  SOURCE OF TRUTH      ayon-agentic-instructions/  (git, versioned, pushable)
                         AGENTS.md, constitution, .agents/{skills,agents,checks},
                         goose recipes, zed task fragment, addon fragments,
                         and the sync tool
    -> single place to edit shared SDD content

L2  PER-REPO LINKAGE     <repo>/.agents-main -> ../ayon-agentic-instructions  (symlink)
    (uncommitted)        <repo>/.git/info/exclude  hides it                     (G4,G5)
                         core.hooksPath -> <ROOT>/.githooks-shared (absolute)   (G2)
                         post-checkout re-links inside new worktrees            (G1,G3)
    -> shared content reaches every repo AND every worktree, zero commits

L3  COMMITTED MINIMUM    <repo>/AGENTS.md                  (the ONE keystone file, X1)
    (upstreamable)       <repo>/.specify/ + speckit command sets  (optional per repo)
    -> works for teammates, CI, and the Copilot cloud agent
```

**Why L2 is uncommitted and L3 is committed:** L2 is machine-specific (absolute paths,
a symlink to a sibling checkout) and must never appear in an upstream PR. L3 is genuinely
useful to everyone and is the only thing a cloud agent (which gets a plain `git clone`,
no symlinks to siblings, no local hooks) can see.

> **Critical corollary:** the Copilot **cloud** agent sees **only L3**. Any instruction
> that must survive in CI has to be *in* the repo. Design `AGENTS.md` so it is
> self-sufficient, and treat `.agents-main/` as an *enrichment*, not a dependency.

---

## 4. Implementation phases

### Phase A — L0 user-global layer (no repo is touched)

Highest value per unit of risk. Do this first; it alone removes the two stated limitations.

**A1. Global Zed tasks.**
Create `~/.config/zed/tasks.json`. Port every task from `<ROOT>/.zed/tasks.json`, but
make each one work from *any* project by pinning the workspace root:

```json
{
  "label": "AYON / Upload addon to server and restart",
  "command": "uv",
  "args": ["run", "upload-to-addon-folder", "-f", "$ZED_FILE", "--debug"],
  "cwd": "${AYON_WORKSPACE_ROOT:/Users/jakub/CODE/__YNPUT}",
  "reveal": "always",
  "hide": "on_success"
}
```

- `cwd` may point outside the worktree (Z7) — this is what makes `uv run` resolve
  `<ROOT>/pyproject.toml` from inside `ayon-nuke`.
- Always use the `${VAR:default}` form or the task vanishes from the modal (Z8).
- `$ZED_RELATIVE_FILE` is relative to the *current* worktree, so inside `ayon-nuke` it
  no longer resolves against `<ROOT>`. **Switch the file-taking tasks to `$ZED_FILE`
  (absolute)** and confirm each `src/jeza_ynput_dev_workspace/*.py` entry point accepts
  an absolute path. Fix the scripts if they don't.
- Keep `<ROOT>/.zed/tasks.json` only for tasks that are genuinely root-only.

*Acceptance:* opening `ayon-nuke` alone in Zed shows the AYON tasks in the task modal.
*Verify:* `test -f ~/.config/zed/tasks.json && python3 -c "import json;json.load(open('$HOME/.config/zed/tasks.json'))"` then open `zed <ROOT>/ayon-flame` and inspect `task: spawn`.

**A2. Global Zed agent instructions.**
Create `~/.config/zed/AGENTS.md` (Z2): who the user is, the `<ROOT>` multi-repo layout,
the AYON house rules, and an instruction to look for `.agents-main/AGENTS.md`. Keep it
short — it is prepended to every request in every project.

*Verify:* file exists; Zed agent panel reports personal instructions loaded.

**A3. Global goose hints.**
Create `~/.config/goose/AGENTS.md` with the same content (N6). Symlink it to avoid drift:
`ln -s ~/.config/zed/AGENTS.md ~/.config/goose/AGENTS.md`.

*Verify:* `goose run --no-session -q -t "In one line, name the workspace root you were told about."` from inside `ayon-flame` mentions `__YNPUT`.

**A4. Global skills, shared by Zed *and* goose.**
`~/.agents/skills/` is read by both (N2, Z3) from any directory. Move the three
workspace skills there and symlink back so `<ROOT>` keeps working:

```bash
mv <ROOT>/.agents/skills/<name> ~/.agents/skills/<name>
ln -s ~/.agents/skills/<name> <ROOT>/.agents/skills/<name>
```

*Acceptance:* `cd <ROOT>/ayon-nuke && goose skills list` lists `harsh-code-review`
(it currently does **not** — that is the N1 defect).
*Verify:* `cd <ROOT>/ayon-nuke && goose skills list | grep harsh-code-review`

**A5. Enable subagents.**
Set `GOOSE_MODE=auto` for SDD sessions, or the delegation designed in Phase E silently
no-ops (N10). Do **not** flip the global default silently — prefer per-recipe/per-run
scoping and tell the user what changed.

---

### Phase B — L1 central repository

Restructure `ayon-agentic-instructions` into the source of truth. Keep the existing good
content (`AGENTS.md` is already solid) and the existing committed symlinks
(`CLAUDE.md -> AGENTS.md`, `.kilo -> .agents`).

**B1. Target layout.**

```
ayon-agentic-instructions/
  AGENTS.md                     # generic AYON addon instructions (exists; extend with SDD)
  CLAUDE.md -> AGENTS.md        # exists
  .kilo -> .agents              # exists
  memory/
    ayon-constitution.md        # the AYON SDD constitution (see B2)
  fragments/
    addon.md                    # generic addon repo instructions
    core.md                     # ayon-core specifics
    launcher.md                 # ayon-launcher specifics
    host-integration.md         # nuke/flame/resolve/hiero shared host-addon rules
  .agents/
    skills/                     # exists — shared skills (Zed + goose + Claude)
    agents/                     # exists — explorer.md, reviewer.md (see B3)
    checks/                     # NEW — `goose review` checks (N12)
    REVIEW.md                   # NEW — scoped review instructions (N12)
  recipes/                      # NEW — shared goose recipes (see Phase E)
  zed/
    tasks.fragment.json         # NEW — canonical global Zed tasks (source for A1)
  tools/
    ayon-sdd                    # NEW — the sync CLI (see Phase D)
  README.md
```

**B2. Write the AYON constitution** → `memory/ayon-constitution.md`.
This is the Spec Kit `constitution.md` content, AYON-flavoured. Derive it from facts
already in `ayon-agentic-instructions/AGENTS.md` — do not invent principles. Cover:

- Addon anatomy: `client/`, `server/`, `package.py`, `create_package.py`.
- Pipeline contracts are functional, not cosmetic: Pyblish `order`, `hosts`, `families`,
  `productBaseType`, `representations`, creator/loader identifiers.
- Client settings paths must stay aligned with server settings models **and** defaults;
  settings keys commonly use the exact Python class name, so renaming a plugin is a
  multi-file change.
- Compatibility imports for multiple AYON Core versions must be preserved.
- Ruff config is authoritative: 79 columns, 4 spaces, double quotes, `E`/`F`/`W`.
- Vendored code (`client/**/vendor/`) is excluded from lint/format.
- Host client code cannot be imported in a plain interpreter; keep GUI work out of
  headless/farm startup paths.
- **Verification ladder** (no test framework exists in most addons — do not add one):
  `ruff check .` → `ruff format --check .` → `python create_package.py --skip-zip`
  → host-app validation described, not executed.

**B3. Subagent definitions** → `.agents/agents/`.
`explorer.md` and `reviewer.md` already exist and already use `model: ollama/ornith:9b`.
Extend with SDD roles: `spec-reviewer`, `settings-auditor` (client↔server settings
drift), `packaging-validator`. Frontmatter: `name`, `description`, `model`.
Point the cheap, mechanical ones at local models (§2.6, N9).

**B4. Review checks** → `.agents/checks/*.md` + `.agents/REVIEW.md` (N12).
One check per invariant from B2, e.g. `settings-alignment.md`, `pyblish-contracts.md`,
`ruff-conformance.md`, `vendor-exclusion.md`. These become the Phase-4 (Verify) gate.

*Verify:* `cd ayon-agentic-instructions && goose review --dry-run --checks-only` lists them.

---

### Phase C — L3 committed per-repo minimum

For each of `ayon-core`, `ayon-launcher`, `ayon-batch-delivery`, `ayon-nuke`,
`ayon-flame`, `ayon-resolve`, `ayon-hiero`.

**C1. `AGENTS.md` at each repo root.** This is the **only** file that must be committed,
because it is the single file all five agents read (X1) and the only thing the Copilot
cloud agent will see (§3 corollary). Structure:

```markdown
# <repo> — agent instructions

## Shared AYON instructions
Generic AYON addon conventions, the SDD constitution, and shared skills live in the
`ayon-agentic-instructions` repository. If `.agents-main/` exists in this working
directory it is a local checkout of that repository — read `.agents-main/AGENTS.md`
and `.agents-main/memory/ayon-constitution.md` first.
If it does not exist, continue with the repository-local rules below; they are
self-sufficient.

## Repository specifics
<build, lint, package commands; architecture; contracts; validation ladder>

## Spec-Driven Development
<the /speckit.* flow and where specs live>
```

- **Fix the dead reference:** `ayon-nuke/AGENTS.md` currently says `.ayon-main/AGENTS.md`;
  the symlink is `.agents-main`. Correct it.
- **`ayon-batch-delivery` conflict (X6):** it has `.github/copilot-instructions.md`,
  which Zed picks **before** `AGENTS.md` (Z4). Either fold that content into `AGENTS.md`
  and delete the old file, or make `copilot-instructions.md` a pointer. Do not leave two
  divergent sources.
- Generate the repo-specific sections from what is actually in each repo
  (`ruff.toml`, `create_package.py`, `pyproject.toml`, `.github/workflows/`). **Do not
  guess commands** — read them.
- `ayon-flame`, `ayon-resolve`, `ayon-hiero`, `ayon-core`, `ayon-launcher` have no
  agentic files at all; these are new files.

*Verify:* `for r in ...; do test -f $r/AGENTS.md || echo "MISSING $r"; done`

**C2. Install Spec Kit per repo.**

```bash
uv tool install specify-cli
cd <repo>
for a in goose zed copilot kilocode; do
  specify init . --here --force --non-interactive --integration "$a" --ignore-agent-tools
done
```

Verified to stack cleanly (S2). Then overwrite `.specify/memory/constitution.md` with
(or symlink it to) `.agents-main/memory/ayon-constitution.md`.

*Acceptance:* `goose recipe list | grep -c speckit` = 10 and
`goose skills list | grep -c speckit` = 10 inside the repo.

**C3. Decide committed vs ignored per repo — ask the user, do not assume.**
`.specify/` + the four command sets is ~40 files. Committing them upstream to
`ynput/*` is a policy decision.

- **Recommended:** commit in `ayon-batch-delivery` (the user's own domain addon)
  and keep it local-only in the shared `ynput` repos until the team agrees.
- For local-only repos, add the paths to `.git/info/exclude` (G4) — **never** to the
  committed `.gitignore`.

Present the choice with this trade-off: local-only keeps upstream clean but makes the
speckit commands invisible to the Copilot cloud agent and to CI.

---

### Phase D — L2 linkage and worktree distribution

This is the part that replaces the current `ayon-nuke` prototype.

**D1. Shared hooks directory** → `<ROOT>/.githooks-shared/post-checkout`.
One file for all repos, referenced by **absolute** path (G2), so nothing is committed
and worktrees inherit it. Rewrite the existing `ayon-nuke/.githooks/post-checkout` to:

1. Keep the "new linked worktree" guard from the existing hook — it is correct:
   `$1` all zeros **and** `$3` = 1 **and** `git rev-parse --git-dir` != `--git-common-dir` (G1).
2. **Replace `git clone` with a symlink** to the single local checkout:
   `ln -sfn <ROOT>/ayon-agentic-instructions "$WORKTREE/.agents-main"`.
   Rationale: the clone is a network hit and goes stale immediately; a symlink is always
   current and free. Resolve `<ROOT>` from the hook's own location, not a hardcoded string.
3. Link `.zed` if Z12 verifies: `ln -sfn <ROOT>/.zed "$WORKTREE/.zed"`.
4. Copy `.env` if present in `$GIT_COMMON_DIR/..` (worktrees don't inherit it — G3).
5. Be idempotent and never fail the checkout (`exit 0` on every path).

**D2. Wire each repo, without committing anything.**

```bash
git -C <repo> config core.hooksPath <ROOT>/.githooks-shared   # absolute (G2)
ln -sfn ../ayon-agentic-instructions <repo>/.agents-main
printf '/.agents-main\n/.zed\n' >> <repo>/.git/info/exclude   # NO trailing slash (G5)
```

`.git/info/exclude` is shared with every linked worktree (G4), so this is a one-time
per-repo step that also covers all future worktrees.

*Acceptance:* `git -C <repo> status --porcelain` is clean after creating the symlinks.
*Verify:* `git -C <repo> check-ignore -v .agents-main` resolves to the main `.git/info/exclude`.

**D3. ⚠ VERIFY FIRST — the symlinked `.zed` experiment.**
Z12 says a symlinked `.zed` is force-scanned even when external. This is read from the
source but **not runtime-verified**. Before relying on it:

```bash
ln -s <ROOT>/.zed <ROOT>/ayon-flame/.zed
zed <ROOT>/ayon-flame     # trust the worktree, then open the task modal
```

- **If the tasks/settings appear:** use it, and note the JSON-autocomplete caveat (Z14).
- **If they do not:** fall back to **A1 global tasks**, which is documented, supported,
  and already covers the requirement. **Do not** build a workaround. Remove the symlink.

Note `ayon-nuke/.zed/` is currently an empty dir — delete it before symlinking.

**D4. Zed `create_worktree` task.**
Move the existing `Utils / Set up new worktree` task from `<ROOT>/.zed/tasks.json` into
`~/.config/zed/tasks.json` so it fires for worktrees created from **any** repo (Z1, Z6).
Change it to invoke `<ROOT>/.githooks-shared/post-checkout`-equivalent logic (or the
D5 CLI) instead of `cp -R`, so the Zed path and the git path share one implementation.
Keep `"hooks": ["create_worktree"]`, `"hide": "on_success"`.

Two entry points cover both ways worktrees get made: git CLI (D1) and Zed's picker (D4).

**D5. The `ayon-sdd` CLI** → `ayon-agentic-instructions/tools/ayon-sdd`.
One idempotent tool that performs D2 and is the single implementation behind D1/D4.
Python + `click` (already a `<ROOT>` dependency); expose it as a `[project.scripts]`
entry in `<ROOT>/pyproject.toml` so `uv run ayon-sdd` works and Zed tasks can call it.

```
ayon-sdd link   [--repo PATH ...] [--all]  # symlinks + hooksPath + info/exclude
ayon-sdd status [--all]                    # what's linked/stale/missing, exit 1 if drift
ayon-sdd init-speckit --repo PATH          # C2 for the 4 integrations
ayon-sdd worktree-setup --worktree PATH --main PATH   # called by hook + Zed task
ayon-sdd doctor                            # asserts every §2 invariant on this machine
```

`doctor` should assert: `~/.config/zed/tasks.json` parses; `~/.config/goose/AGENTS.md`
exists; `goose skills list` from inside a repo shows the shared skills (N1 regression
test); each repo's `.agents-main` resolves; `check-ignore` is satisfied; `core.hooksPath`
is absolute and exists.

*Verify:* `uv run ayon-sdd doctor` exits 0; `uv run ayon-sdd status --all` shows no drift.

---

### Phase E — SDD workflow and local-inference recipes

**E1. Map SDD to the tools we now have** (do not invent a parallel workflow):

| SDD phase | Mechanism | Artifact |
| --- | --- | --- |
| Constitution | `/speckit.constitution` seeded from `memory/ayon-constitution.md` | `.specify/memory/constitution.md` |
| 1 Specify | `/speckit.specify`, `/speckit.clarify` | `specs/NNN-slug/spec.md` |
| 2 Plan | `/speckit.plan` | `plan.md`, `research.md`, `data-model.md` |
| 3 Implement | `/speckit.tasks` → `/speckit.implement` | `tasks.md` + code |
| 4 Verify | `/speckit.analyze`, `goose review` with `.agents/checks/` (N12), then the B2 ladder | review report |

**E2. Shared goose recipes** → `ayon-agentic-instructions/recipes/`.
Make them reachable from every repo via
`export GOOSE_RECIPE_PATH="<ROOT>/ayon-agentic-instructions/recipes"` (N7), and register
the useful ones in `~/.config/goose/config.yaml` under `slash_commands` (the user already
has six such entries, so follow that existing pattern).

Recipes to write — each `goose recipe validate`-clean:

- `ayon-addon-spec` — writes an AYON-aware `spec.md` (settings impact, host constraints,
  pipeline contracts touched).
- `ayon-settings-audit` — **local model**; diff `client/` plugin classes against
  `server/settings/` models + defaults and report drift.
- `ayon-package-check` — **local model**; run the B2 verification ladder, return
  structured pass/fail.
- `ayon-worktree-bootstrap` — wraps `ayon-sdd worktree-setup`.
- `ayon-sdd-orchestrator` — top-level recipe with `sub_recipes` for the above.

**E3. Local-inference offload.**
`GOOSE_LEAD_MODEL` is gone (N9). Use **per-recipe `settings`**:

```yaml
# ayon-settings-audit.yaml
settings:
  goose_provider: ollama
  goose_model: qwen2.5-coder:3b     # already installed
  max_turns: 25
```

Reserve local models for mechanical, high-token, low-judgement work: lint triage,
settings-drift diffing, docstring checks, packaging validation, commit/PR message drafts.
Keep specify/plan/implement on the cloud model. Also consider `GOOSE_FAST_MODEL` for
auxiliary calls. Remember **`GOOSE_MODE=auto`** (A5/N10) or sub-delegation won't run.

**E4. Zed and Kilo parity.**
Spec Kit already generates Zed skills and Kilo commands (S3). Additionally symlink the
shared skills into each repo so Zed sees them project-locally (Z3, N3):
`ln -sfn ../../.agents-main/.agents/skills/<name> <repo>/.agents/skills/<name>`.
Both symlink shapes are verified to work with goose (N3).

---

### Phase F — Remote / CI (do after A–E are working locally)

**F1. Copilot cloud agent.** It sees **only committed files** (§3). Ensure each repo's
`AGENTS.md` is self-sufficient (C1). Optionally add
`.github/workflows/copilot-setup-steps.yml` to pre-install `uv`/`ruff` so the cloud agent
can run the B2 ladder.

**F2. Goose in CI.** No official action exists (N13). Follow the documented pattern:
install the CLI in a step with a pinned `GOOSE_VERSION`, write `~/.config/goose/config.yaml`
with **`keyring: false`**, then
`goose run --recipe .goose/recipes/<r>.yaml --no-session -q --output-format json`.
Prefer `response.json_schema` (N8) over scraping stdout.
Start with **one** repo (`ayon-batch-delivery`) and one gate (`ayon-package-check`).

**F3. Optional — local RAG.** Only if A–E leave a real retrieval gap (R3).
Scope it to the **SDD prose corpus** (specs, plans, constitution, `docs/`), not Python
source. `chunkhound` with `nomic-embed-text` via Ollama is the lowest-maintenance option
(R2) and has evidently been trialled here already. Register it as an MCP server in
`~/.config/goose/config.yaml` and, for Zed, in `.zed/settings.json` → `context_servers`
(project-scopable — Z11). **Do not** put it in `agent_servers` (Z10).

---

## 5. Ordering, risk and rollback

| Phase | Risk | Rollback |
| --- | --- | --- |
| A (L0 global) | Very low — touches no repo | delete the `~/.config` files |
| B (central) | Low — its own repo | `git revert` |
| C (committed) | **Medium — modifies shared `ynput` repos** | branch + PR per repo; never push to `main` |
| D (linkage) | Low — symlinks + local git config | `ayon-sdd unlink`; symlinks are ignored via `info/exclude` |
| E (recipes) | Low | delete recipes |
| F (CI/RAG) | Medium | revert workflows |

**Do Phase A first and stop for user confirmation.** It independently removes both
limitations stated in `PLAN.md` and requires no repo changes, so it is the cheapest way
to validate the whole direction.

**Hard gates:**
- Do not push to any `ynput/*` repo without an explicit go-ahead. Use branches + PRs.
- Do not add a test framework to addons that have none (B2).
- Do not edit any repo's committed `.gitignore` for local tooling — use
  `.git/info/exclude` (G4).
- Re-verify D3 before depending on symlinked `.zed`.

---

## 6. Open questions for the user (ask before Phase C)

1. **Commit Spec Kit artifacts upstream?** `.specify/` + 4 command sets ≈ 40 files per
   repo. Which repos may receive them in a PR to `ynput/*`, and which stay local-only?
2. **`ayon-batch-delivery`:** fold `.github/copilot-instructions.md` into `AGENTS.md`,
   or keep both with one as a pointer? (X6/Z4 — they currently conflict.)
3. **Should `AGENTS.md` be committed to the shared `ynput` repos** (`ayon-core`,
   `ayon-nuke`, …) or kept local? Committing is what makes CI and the Copilot cloud
   agent work; not committing keeps upstream untouched.
4. **`GOOSE_MODE=auto`** globally, or only for SDD recipe runs? (N10 — subagents need it.)
5. Which addon is the pilot? Recommendation: **`ayon-batch-delivery`** — it is the user's
   own domain addon, already has `.agents-main` + `.zed`, and has `tests/`.

---

## 7. Definition of done

- [ ] From inside `<ROOT>/ayon-flame` opened alone in Zed: AYON tasks appear in the task
      modal, and the agent panel has the AYON personal instructions. (A1, A2)
- [ ] `cd <ROOT>/ayon-nuke && goose skills list` lists the shared AYON skills. (A4 — fixes N1)
- [ ] `ayon-agentic-instructions` holds the constitution, fragments, checks, recipes and
      the `ayon-sdd` tool, and is pushed. (B)
- [ ] Every in-scope repo has a correct, self-sufficient `AGENTS.md` with no dead
      `.ayon-main` reference. (C1)
- [ ] In the pilot repo: `goose recipe list | grep -c speckit` = 10 and
      `goose skills list | grep -c speckit` = 10. (C2)
- [ ] `uv run ayon-sdd doctor` exits 0 for all in-scope repos. (D5)
- [ ] `git -C <repo> status --porcelain` is clean despite the local symlinks. (D2)
- [ ] A new worktree — created **both** via `git worktree add` and via Zed's picker —
      comes up with `.agents-main` resolving and `.env` present. (D1, D4)
- [ ] `goose review` runs the AYON checks in the pilot repo. (B4)
- [ ] D3 has an explicit **verified / falsified** result recorded in this file.
- [ ] Phase F only started after A–E are green.

---

## 8. Appendix — evidence index

- **[EMPIRICAL]** items were executed on this workstation on 2026-09-02 (git worktree
  hook firing, absolute `hooksPath`, `info/exclude` worktree sharing and the trailing-slash
  trap, goose skill visibility boundary, goose symlink resolution, four-way Spec Kit
  stacking and goose's discovery of the resulting skills/recipes).
- **Zed** facts: `zed-industries/zed` @ `main` — `crates/paths/src/paths.rs`,
  `crates/task/src/task_template.rs`, `crates/project/src/task_inventory.rs`,
  `crates/prompt_store/src/prompts.rs`, `crates/worktree/src/worktree.rs`,
  `crates/settings_content/src/{project,agent}.rs`; docs `zed.dev/docs/{tasks,ai/instructions,ai/skills,ai/mcp,ai/external-agents,windows-and-projects,reference/cli}`.
  Note `zed.dev/docs/ai/rules` is **404** — the Rules system was replaced by
  Instructions + Skills; ignore any older guidance citing it.
- **Goose** facts: the project moved to the **AAIF** — repo `aaif-goose/goose`, docs
  **`goose-docs.ai`** (`block.github.io/goose` now redirects). Source:
  `crates/goose/src/hints/{load_hints,import_files}.rs`, `crates/goose/src/recipe/`,
  `crates/goose/src/providers/local_inference.rs`.
- **Spec Kit**: `github/spec-kit` @ HEAD — `src/specify_cli/integrations/`,
  `src/specify_cli/commands/init.py`, `templates/commands/`, `scripts/bash/`.
- **Copilot**: `docs.github.com/en/copilot/reference/custom-instructions-support`,
  `.../concepts/prompting/response-customization`,
  `.../how-tos/.../add-repository-instructions`.
- **Kilo**: `kilo.ai/docs/customize/{custom-rules,agents-md}`.
- **AGENTS.md**: `agents.md`, `github.com/agentsmd/agents.md`.
- Full research reports are retained in the session workspace:
  `zed-research.md`, `goose-research.md`.
