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
5b. **Everything must be reproducible.** No step in this plan may exist only as a
   command you once typed. Every manual action you perform during Phases A–F must end
   up as a script in `<ROOT>/src/jeza_ynput_dev_workspace/` and be reachable from a Zed
   task. The test is Phase G: a brand-new, empty workspace folder must reach the same
   state with **one** Zed task and no manual steps. If you cannot script it, say so
   explicitly instead of doing it by hand.
6. Never modify: `__TESTs/`, `.venv`, `*.worktrees/`, `worktrees/`, `.env*`, `uv.*`,
   or any `ayon-*` folder not listed in §1.
7. Never commit to `ayon-backend`, `ayon-frontend`, `ayon-docker`.
8. **§6 contains binding decisions, not open questions.** They were answered by the user
   on 2026-09-02. Read §6 **before** Phase C. Do not re-ask them, and do not substitute
   your own preference — especially the per-repo **branch table** (§6 D1). Writing to
   the wrong branch is the single most damaging mistake available to you here.

---

## 1. Scope

**Workspace root** (`<ROOT>`): `/Users/jakub/CODE/__YNPUT` — a personal, unpublished wrapper.

> **`<ROOT>` is itself a git repository:** `github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace`.
> Tracked at top level: `.zed/`, `.agents/`, `src/`, `pyproject.toml`, `ruff.toml`,
> `resources/`, `PLAN.md`, `SDD-instructions.md`. All `ayon-*` siblings are gitignored.
> **This is what makes Phase G possible** — a future replacement for `__YNPUT` is just a
> clone of this repo, so the workspace tooling travels with it. Treat `<ROOT>/src` as the
> versioned, reproducible home for all workspace-level automation.

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
```

**Existing `src/` conventions — follow them for all new scripts:**
one module per command; a module-level function of the same name as the entry point;
`click` for argument parsing (used by `create_addon_package`, `launch_ayon_app`,
`upload_to_addon_folder`, `git_commit_info_extraction`); Google-style docstrings with
`Args:`/`Returns:`; exported from `__init__.py` via `__all__`; registered in
`[project.scripts]` in `<ROOT>/pyproject.toml`; invoked from Zed as `uv run <name>`.

```
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

Five layers. Each solves a specific failure mode.

```
L0  USER-GLOBAL          ~/.config/zed/{tasks.json,AGENTS.md}
    (no repo touched)    ~/.config/goose/AGENTS.md
                         ~/.agents/skills/  ~/.agents/agents/
    -> fixes: "I lose Zed tasks and agent context inside a repo"  (Z1,Z2,Z3,N2,N6)
    -> GENERATED, never hand-edited: written by `ayon-sdd install-global` (Phase G)

LW  WORKSPACE TOOLING    <ROOT>/src/jeza_ynput_dev_workspace/   (git: Jeza-Ynput-Dev-Workspace)
    (the reproducer)     <ROOT>/pyproject.toml  [project.scripts]
                         <ROOT>/.zed/tasks.json  (workspace-only tasks)
                         <ROOT>/.githooks-shared/
    -> every action in this plan is a script here; a new workspace root is a clone
    -> owns the MACHINE-shaped concerns: paths, linking, hooks, global config

L1  SOURCE OF TRUTH      ayon-agentic-instructions/  (git, versioned, pushable)
                         AGENTS.md, constitution, .agents/{skills,agents,checks},
                         goose recipes, zed task fragment, addon fragments
    -> single place to edit shared SDD CONTENT (no machine-specific paths)

L2  PER-REPO LINKAGE     <repo>/.agents-main -> ../ayon-agentic-instructions  (symlink)
    (uncommitted)        <repo>/.git/info/exclude  hides it                     (G4,G5)
                         core.hooksPath -> <ROOT>/.githooks-shared (absolute)   (G2)
                         post-checkout re-links inside new worktrees            (G1,G3)
    -> shared content reaches every repo AND every worktree, zero commits
    -> applied by `ayon-sdd link`, never by hand

L3  COMMITTED MINIMUM    <repo>/AGENTS.md                  (the ONE keystone file, X1)
    (upstreamable)       <repo>/.specify/ + speckit command sets  (optional per repo)
    -> works for teammates, CI, and the Copilot cloud agent
```

**LW vs L1 — the split that keeps this reproducible.** Put a thing in **LW** if it
mentions an absolute path, a machine, or a tool version. Put it in **L1** if it is
AYON knowledge that a teammate on another machine would also want. LW is *how*, L1 is
*what*. Violating this is what makes setups unreproducible: never hardcode
`/Users/jakub/...` into `ayon-agentic-instructions`, and never put AYON pipeline
conventions into `src/`.

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

> **Reproducibility rule for this phase (§0.5b):** do not hand-write these files as a
> one-off. Author them as **templates under `<ROOT>/src/jeza_ynput_dev_workspace/templates/`**
> and have `ayon-sdd install-global` render them into `~/.config/...`. Hand-editing is
> allowed only while prototyping A1–A5; before Phase A is marked done, the exact same
> result must be obtainable from `uv run ayon-sdd install-global` on a clean machine.
> Everything in L0 is **generated output**, and the templates are the source.

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

**A5. Verify subagents are enabled — already done (§6 D3).**
`GOOSE_MODE: auto` is **already set** in `~/.config/goose/config.yaml` (verified
2026-09-02). **Verify only; do not modify the user's goose config.**
*Verify:* `grep -n 'GOOSE_MODE' ~/.config/goose/config.yaml` shows `auto`. If it does
not, report it and stop — Phase E delegation depends on it (N10).

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
  README.md
```

> **No `tools/` here.** The `ayon-sdd` CLI lives in `<ROOT>/src` (LW), not in this repo —
> see §3 and D5. This repo holds portable AYON *content*; anything that knows about
> absolute paths, this machine, or this workspace belongs in `<ROOT>/src`.
> `zed/tasks.fragment.json` is the one borderline case: keep it **path-free** (use
> `${AYON_WORKSPACE_ROOT:...}`) so `ayon-sdd install-global` can render it anywhere.

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
- **`ayon-batch-delivery` conflict (X6) — decided (§6 D2):** fold any unique content from
  `.github/copilot-instructions.md` into `AGENTS.md`, then **delete** the old file.
  Zed then falls through to `AGENTS.md` (Z4), which is the fix. Note the accepted
  regression for Copilot Chat on github.com in the commit message.
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

**C3. Commit the artifacts on the dedicated branch — decided (§6 D1).**

All seven target repos have a dedicated branch, so `.specify/` + the four command sets
**and** `AGENTS.md` are **committed**, not hidden.

- **Assert the branch before writing** to any repo (see the §6 D1 table). `ayon-nuke`
  uses `enhancement/developing-agentic-workflow-basic`; the other six use
  `agentic-sdd-dev`. On mismatch, **stop and report** — never switch branches, never
  commit to `develop`/`main`.
- Do **not** add these paths to `.git/info/exclude` in these seven repos.
- Commit only; **do not open PRs** to `ynput/*` — that stays a human decision.

*Verify:* `git -C <repo> status --short` is clean and
`git -C <repo> log --oneline -1` shows the SDD commit on the expected branch.

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

> **Result: VERIFIED — [EMPIRICAL] 2026-09-03.** Deleted the empty `ayon-nuke/.zed`,
> then ran `ln -s /Users/jakub/CODE/__YNPUT/.zed ayon-flame/.zed` and opened
> `zed ayon-flame` with `RUST_LOG="worktree=trace,project=trace,task=trace"`. The
> worktree scanner log shows it descending into the symlink exactly like a real
> directory: `DEBUG [worktree] detected hidden file: ".zed"` →
> `TRACE [worktree] scanning directory ".zed"` → `DEBUG [worktree] detected hidden
> file: ".zed/tasks.json"` (also `settings.json`, `debug.json`,
> `launch_subprocess.py` — the real contents of `<ROOT>/.zed`, proving it is a live
> symlink, not a copy). No error/permission-denied/external-skip log line appeared.
> This is the exact discovery path Z12 predicted from source. GUI screenshot
> confirmation of the task modal itself was not possible in this environment (no
> Screen Recording / Accessibility permission for automation), but worktree-level
> file discovery is the necessary and sufficient precondition Zed's task inventory
> consumes, so the mechanism is considered proven. **Decision: use the symlinked
> `.zed` approach (D2/D4)**, not the A1 global-tasks-only fallback. The experiment
> symlink was removed after the test; `ayon-flame`/`ayon-nuke` git status stayed
> clean throughout (`git status --porcelain` empty before and after in both repos).

**D4. Zed `create_worktree` task.**
Move the existing `Utils / Set up new worktree` task from `<ROOT>/.zed/tasks.json` into
`~/.config/zed/tasks.json` so it fires for worktrees created from **any** repo (Z1, Z6).
Change it to invoke `<ROOT>/.githooks-shared/post-checkout`-equivalent logic (or the
D5 CLI) instead of `cp -R`, so the Zed path and the git path share one implementation.
Keep `"hooks": ["create_worktree"]`, `"hide": "on_success"`.

Two entry points cover both ways worktrees get made: git CLI (D1) and Zed's picker (D4).

**D5. The `ayon-sdd` CLI** → `<ROOT>/src/jeza_ynput_dev_workspace/ayon_sdd.py`.
One idempotent tool that performs D2 and is the **single implementation** behind D1, D4
and Phase G. It lives in **LW**, not in `ayon-agentic-instructions`, because every one of
its operations is machine-shaped (absolute paths, git config, symlinks) — see §3.
Python + `click`, following the existing `src/` conventions (§1.1). Register it in
`__init__.py`/`__all__` and in `<ROOT>/pyproject.toml` `[project.scripts]` as
`ayon-sdd = "jeza_ynput_dev_workspace:ayon_sdd"`, so `uv run ayon-sdd` works and Zed
tasks can call it.

**The hook and the Zed task must both be thin wrappers that shell out to this CLI.**
Do not let `post-checkout` (D1) and the `create_worktree` task (D4) grow independent
copies of the same logic — that is precisely the drift this plan exists to prevent.

```
ayon-sdd link   [--repo PATH ...] [--all]  # symlinks + hooksPath + info/exclude
ayon-sdd unlink [--repo PATH ...] [--all]  # full reversal (see §5 rollback)
ayon-sdd status [--all]                    # what's linked/stale/missing, exit 1 if drift
ayon-sdd init-speckit --repo PATH          # C2 for the 4 integrations
ayon-sdd worktree-setup --worktree PATH --main PATH   # called by hook + Zed task

> **D4 real-world GUI verification (2026-09-03).** The `git worktree add` path (D1) was
> verified in-session; the Zed-picker path (D4) could only be verified indirectly at the
> time (no Screen Recording/Accessibility permission for GUI automation). The user then
> tested it for real by creating a worktree through Zed's own picker and running the task
> from there. Result: `uv run ayon-sdd worktree-setup ...` failed to spawn `ayon-sdd`
> (`error: Failed to spawn: \`ayon-sdd\` / Caused by: No such file or directory`), while
> the sibling `Dev / Upload addon to server and restart` task — using the identical
> `"cwd": "${AYON_WORKSPACE_ROOT:...}"` token and the same `uv run <entrypoint>` pattern —
> succeeded. Root cause could not be reproduced deterministically outside Zed (PATH,
> login-shell env, and directory-tree project discovery were all ruled out by simulation),
> but `create_worktree`-hook-triggered tasks fire immediately at worktree creation, a
> different execution path from a manually-invoked task, and `uv run <name>` normally
> resolves the project by walking up from `cwd`. **Fix:** make project resolution
> explicit instead of implicit — pass `uv run --project ${AYON_WORKSPACE_ROOT:...} ayon-sdd
> ...` so `uv` never has to discover the project directory on its own. This removes the
> only remaining variable between the working and failing task. Verified after the fix:
> `uv run --project <ROOT> ayon-sdd worktree-setup --dry-run` succeeds from an unrelated
> `cwd` (`/tmp`) and from inside the affected worktree itself.
ayon-sdd install-global                    # writes the whole L0 layer (Phase A)
ayon-sdd bootstrap [--root PATH]           # Phase G: whole workspace from scratch
ayon-sdd doctor                            # asserts every §2 invariant on this machine
```

**Cross-cutting requirements for every subcommand** — these are what make the setup
reproducible rather than a one-off:

- **Idempotent.** Running it twice changes nothing the second time and exits 0.
- **`--dry-run` on every mutating subcommand**, printing the exact filesystem and
  `git config` operations. This is how the user reviews a change before it lands.
- **No hardcoded `/Users/jakub/...`.** Resolve `<ROOT>` from the installed package
  location or an `AYON_WORKSPACE_ROOT` override, never a literal. This is the single
  most important rule for Phase G to work.
- **Never destructive without `--force`.** Back up any file it would overwrite
  (notably `~/.config/zed/tasks.json`, which may already exist).
- Refuse to run against out-of-scope repos (§1) and hard-refuse
  `ayon-backend`/`ayon-frontend`/`ayon-docker`.

`doctor` should assert: `~/.config/zed/tasks.json` parses; `~/.config/goose/AGENTS.md`
exists; `goose skills list` from inside a repo shows the shared skills (N1 regression
test); each repo's `.agents-main` resolves; `check-ignore` is satisfied; `core.hooksPath`
is absolute and exists. `doctor` **is the regression suite for this plan** — every
invariant in §2 that can be asserted cheaply should become a `doctor` check, so drift is
detected rather than discovered.

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
auxiliary calls. **`GOOSE_MODE=auto`** is already set (§6 D3/A5), so sub-delegation runs.

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

### Phase G — Reproducibility: scripting the whole setup and bootstrapping a new workspace root

**Goal:** a future replacement for `__YNPUT` — a new, empty workspace folder on this or
any machine — reaches the full A–F state by opening it in Zed and running **one task**.
Nothing in this plan may survive only as a command that was typed once.

This phase is not "extra work at the end". Phases A–F each *produce* a script here; G is
where they are consolidated, ordered, and proven on a clean folder.

**G0. The bootstrap chain (this is what makes it possible).**
`<ROOT>` is itself the git repo `jakubjezek001/Jeza-Ynput-Dev-Workspace` (§1), tracking
`.zed/`, `.agents/`, `src/` and `pyproject.toml`. So:

```
clone Jeza-Ynput-Dev-Workspace  ->  brings .zed/ + src/ + pyproject.toml
        |
        v
uv sync                          ->  installs the [project.scripts] entry points
        |
        v
uv run ayon-sdd bootstrap        ->  L0 + repos + L1 + L2 + speckit + verify
```

There is no chicken-and-egg problem as long as **the bootstrap entry point does not
require an existing workspace to run**. Handle the very first step with one of these two
verified-supported options — pick one and document it in `<ROOT>/README.md`:

- **(a) Two-step, recommended:** `git clone <workspace-repo> <NEW_ROOT> && cd <NEW_ROOT> && uv sync && uv run ayon-sdd bootstrap`.
  Boring, transparent, no packaging work.
- **(b) One-shot standalone script:** a single self-contained
  `src/jeza_ynput_dev_workspace/bootstrap_workspace.py` carrying **PEP 723 inline
  script metadata** (`# /// script` … `dependencies = ["click"]` … `# ///`) so
  `uv run <url-or-path>` executes it with zero prior install. It then performs (a).
  ⚠ Do **not** attempt `uvx --from git+<workspace-repo> ayon-sdd`: `<ROOT>/pyproject.toml`
  pulls heavy pins (`OpenColorIO`, `opentimelineio`, `pywin32`, git-URL deps like `acre`
  and `appdirs`) and resolving them just to create some symlinks is slow and brittle.
  If you want this path, first add a lightweight `[project.optional-dependencies]`
  extra that the bootstrap alone depends on.

**G1. Consolidate every manual step into `<ROOT>/src/jeza_ynput_dev_workspace/`.**
New modules, following the existing `src/` conventions (§1.1 — one module per command,
`click`, Google docstrings, exported in `__init__.py`, registered in
`[project.scripts]`):

| Module | Entry point | Replaces manual work from |
| --- | --- | --- |
| `ayon_sdd.py` | `ayon-sdd` | D5 — the umbrella CLI; all subcommands below |
| `sdd_install_global.py` | `ayon-sdd-install-global` | **Phase A** — renders L0 from templates |
| `sdd_link_repos.py` | `ayon-sdd-link` | **D2** — symlinks, `hooksPath`, `info/exclude` |
| `sdd_worktree_setup.py` | `ayon-sdd-worktree-setup` | **D1/D4** — the one implementation both the git hook and the Zed task call |
| `sdd_init_speckit.py` | `ayon-sdd-init-speckit` | **C2** — the 4 `specify init` runs |
| `sdd_doctor.py` | `ayon-sdd-doctor` | **§7** — asserts the §2 invariants |
| `bootstrap_workspace.py` | `ayon-workspace-bootstrap` | **G0/G3** — new root from scratch |
| `templates/` | — | the L0 file templates (A1–A4) |

Prefer subcommands on one `ayon-sdd` group over many top-level scripts; list the
individual entry points only if the user wants them bound to separate Zed tasks.

**G2. Reuse what already exists — do not duplicate it.**
`git_clone_all_repos` already clones the full AYON repo set into the cwd. `bootstrap`
must **call that function**, not reimplement cloning. Note it currently clones *every*
repo and `os.chdir`s; for bootstrap you want the §1 in-scope subset and no global
`chdir`. Refactor `initialize_all_clone()` to take an explicit repo list and target path,
keeping the existing `git_clone_all_repos()` entry point behaviour unchanged.

**G3. The bootstrap task itself.**
`ayon-sdd bootstrap [--root PATH] [--dry-run] [--skip-clone]` runs, in order:

1. **Preflight.** Assert `git`, `uv`, `zed`, `goose` are on `PATH` and report versions.
   Warn (do not fail) if `goose`/`zed` are missing — L0 is still writable.
2. **Resolve `<NEW_ROOT>`** from `--root`, else `$AYON_WORKSPACE_ROOT`, else cwd.
   Refuse to run in `$HOME` or `/`.
3. **Clone the in-scope repos** (G2) unless `--skip-clone`.
4. **`install-global`** → the L0 layer (Phase A), backing up anything it overwrites.
5. **Clone/locate `ayon-agentic-instructions`** → the L1 source of truth (Phase B).
6. **`link --all`** → the L2 layer (Phase D2), incl. absolute `core.hooksPath` and
   `.git/info/exclude` entries.
7. **`init-speckit`** for the seven repos listed in §6 D1, asserting the expected branch
   for each before writing (Phase C2/C3).
8. **`doctor`** → fail loudly with a per-check report if anything is off.

Every step idempotent; the whole thing safe to re-run; `--dry-run` prints the plan.

**G4. The Zed task — "initialize agentic workflow here".**
This must live in the **global** `~/.config/zed/tasks.json` (A1), because a brand-new
empty folder has no `.zed/` of its own, and global tasks are the *only* tasks guaranteed
to appear in every project (Z1). That is exactly the property needed here.

```json
{
  "label": "AYON / Bootstrap agentic workspace HERE",
  "command": "uv",
  "args": ["run", "ayon-sdd", "bootstrap", "--root", "$ZED_WORKTREE_ROOT"],
  "cwd": "${AYON_WORKSPACE_ROOT:/Users/jakub/CODE/__YNPUT}",
  "use_new_terminal": true,
  "reveal": "always",
  "hide": "never"
}
```

- `cwd` points at an **existing** workspace so `uv run` resolves its `pyproject.toml`,
  while `--root $ZED_WORKTREE_ROOT` targets the **new** folder. `cwd` outside the
  worktree is explicitly allowed (Z7).
- Use the `${VAR:default}` form or the task is filtered out of the modal (Z8).
- `"hide": "never"` — this is a long, one-off operation; the user wants to read it.
- Pair it with a `"AYON / Doctor"` task (`ayon-sdd doctor`) so verification is one
  keystroke from anywhere.
- **Bootstrapping the very first workspace on a fresh machine** has no existing `cwd` to
  borrow, so it uses G0(a)/(b) from a terminal. Once *any* workspace exists, the Zed task
  covers every subsequent one. State this limitation in the README rather than trying to
  engineer around it.

**G5. Prove it on a clean folder.** This is the acceptance test for the whole plan:

```bash
mkdir -p /tmp/ynput-repro && cd /tmp/ynput-repro
git clone https://github.com/jakubjezek001/Jeza-Ynput-Dev-Workspace.git ws && cd ws
uv sync
uv run ayon-sdd bootstrap --root "$PWD" --dry-run    # review
uv run ayon-sdd bootstrap --root "$PWD"
uv run ayon-sdd doctor                                # must exit 0
```

Then open `/tmp/ynput-repro/ws/ayon-nuke` in Zed and confirm the §7 checklist holds
there. Delete the folder afterwards. If any step needed a manual fix, that fix is a bug
in G1 — fold it back into the scripts and re-run from scratch.

**G6. Document it — required deliverable (§6 D5).** `<ROOT>/README.md` must contain, as
a copy-pasteable sequence someone can follow with no prior knowledge:

1. The **G0(a) chain**: `git clone <workspace-repo> && cd <ws> && uv sync && uv run
   ayon-sdd bootstrap` — including the `--dry-run` review step and `--root` usage.
2. `ayon-sdd bootstrap --all` for the full ~40-repo set vs the default in-scope ten
   (§6 D6).
3. The exact **Zed task names** (`AYON / Bootstrap agentic workspace HERE`,
   `AYON / Doctor`) and where they come from (global `tasks.json`, A1).
4. The **verification** step (`ayon-sdd doctor`) and how to read its report.
5. The **fresh-machine limitation** from G4 (no existing `cwd` to borrow ⇒ first
   workspace is bootstrapped from a terminal, every later one from the Zed task).
6. Prerequisites: `uv`, `git`, `goose`, Zed — and that `GOOSE_MODE: auto` is required
   (§6 D3/N10).

Option (b), the standalone PEP 723 one-shot script, was **rejected** — do not build it
and do not document it. A reproducible setup that nobody can find is not reproducible.

---

## 5. Ordering, risk and rollback

| Phase | Risk | Rollback |
| --- | --- | --- |
| A (L0 global) | Very low — touches no repo | `ayon-sdd install-global --revert`, or delete the `~/.config` files |
| B (central) | Low — its own repo | `git revert` |
| C (committed) | **Medium — modifies shared `ynput` repos** | branch + PR per repo; never push to `main` |
| D (linkage) | Low — symlinks + local git config | `ayon-sdd unlink`; symlinks are ignored via `info/exclude` |
| E (recipes) | Low | delete recipes |
| F (CI/RAG) | Medium | revert workflows |
| G (reproducibility) | Low — consolidation + a scratch-folder test | scripts live in the workspace repo; `git revert` |

**Do Phase A first and stop for user confirmation.** It independently removes both
limitations stated in `PLAN.md` and requires no repo changes, so it is the cheapest way
to validate the whole direction.

**Phase G is not optional and not deferrable to "later".** Write each script as its
phase lands (§0.5b); G is the consolidation and the clean-folder proof, not the moment
you start automating. A plan that only works because of steps someone typed once has
failed its main requirement.

**Hard gates:**
- Do not push to any `ynput/*` repo without an explicit go-ahead. Use branches + PRs.
- Do not add a test framework to addons that have none (B2).
- Do not edit any repo's committed `.gitignore` for local tooling — use
  `.git/info/exclude` (G4).
- Re-verify D3 before depending on symlinked `.zed`.
- **No absolute `/Users/jakub/...` literals inside any script in `<ROOT>/src`** — resolve
  the root from the package location or `AYON_WORKSPACE_ROOT` (D5). A hardcoded home
  directory breaks Phase G on any other machine or folder name.
- **One implementation per behaviour.** The git hook, the Zed task and the bootstrap must
  all call the same `ayon-sdd` subcommand.

---

## 6. Decisions (answered by the user 2026-09-02 — these are binding)

> These were open questions during Phase 1. They are now **settled**. Do not re-ask them;
> implement exactly as stated below. Verified branch state is `[EMPIRICAL]`, checked
> 2026-09-02.

### D1 — Target repos and branches (was Q1 + Q3)

Spec Kit artifacts **and** `AGENTS.md` are **committed** — not local-only — because a
dedicated branch exists in every target repo. Work on these branches only:

| Repo | Branch to commit on |
| --- | --- |
| `ayon-batch-delivery` | `agentic-sdd-dev` |
| `ayon-flame` | `agentic-sdd-dev` |
| `ayon-resolve` | `agentic-sdd-dev` |
| `ayon-hiero` | `agentic-sdd-dev` |
| `ayon-core` | `agentic-sdd-dev` |
| `ayon-launcher` | `agentic-sdd-dev` |
| **`ayon-nuke`** | **`enhancement/developing-agentic-workflow-basic`** ← *not* `agentic-sdd-dev` |

**[EMPIRICAL]** All seven repos were verified checked out on exactly these branches.

- **Before writing to any repo, assert the branch.** If `git -C <repo> rev-parse
  --abbrev-ref HEAD` does not match the table, **stop and report** — do not switch
  branches, and never commit to `develop`/`main`.
- `.git/info/exclude` is therefore **not** used to hide `.specify/` in these seven.
  It remains the correct tool for L2 symlinks (D3/G4).
- No PR is opened to `ynput/*` in this phase. Committing to the branch is the deliverable;
  raising the PR stays a manual human decision.

### D2 — `ayon-batch-delivery` Copilot conflict (was Q2)

**Keep only `AGENTS.md`; delete `.github/copilot-instructions.md`.** Fold any unique
content into `AGENTS.md` first — do not lose it.

This is safe and confirmed by the research, with one caveat to state in the commit message:

- Zed reads `copilot-instructions.md` **before** `AGENTS.md` (Z4/X6). Deleting it makes
  Zed fall through to `AGENTS.md` — this is precisely the fix.
- The Copilot **cloud agent** and **VS Code** both read `AGENTS.md` natively (X2/X1).
- ⚠ **Known regression, accepted:** Copilot **Chat on github.com** honors *only*
  `.github/copilot-instructions.md` (X2). It will therefore see no custom instructions
  in this repo. Accepted deliberately in favour of one source of truth.

### D3 — `GOOSE_MODE=auto` (was Q4)

**Already set globally** by the user in `~/.config/goose/config.yaml`
(`GOOSE_MODE: auto`, line 199) — **[EMPIRICAL]**, verified.

Phase A must therefore **verify, not set**, this value. If already `auto`, report and
move on. Do not rewrite the user's goose config.

### D4 — Pilot repo (was Q5)

**`ayon-batch-delivery`** on branch `agentic-sdd-dev`. Every "pilot repo" reference in
Phases B–F means this repo.

### D5 — Bootstrap entry point (was Q6)

**Option (a):** `git clone && uv sync && uv run ayon-sdd bootstrap`. Do **not** build the
PEP 723 one-shot script.

**Additional requirement:** document the full sequence in a **`README.md` at `<ROOT>`**,
covering clone → `uv sync` → `ayon-sdd bootstrap` → verification, so a new machine or a
future replacement for `__YNPUT` is reproducible from the README alone. This README is a
required deliverable of Phase G, not optional.

### D6 — Bootstrap clone scope (was Q7)

**In-scope ten by default; `--all` for the full ~40-repo set** (the current
`git_clone_all_repos` behaviour, which `--all` must reuse rather than reimplement).

---

## 7. Definition of done

- [ ] From inside `<ROOT>/ayon-flame` opened alone in Zed: AYON tasks appear in the task
      modal, and the agent panel has the AYON personal instructions. (A1, A2)
- [ ] `cd <ROOT>/ayon-nuke && goose skills list` lists the shared AYON skills. (A4 — fixes N1)
- [ ] `ayon-agentic-instructions` holds the constitution, fragments, checks and recipes,
      and is pushed. (B) — note the `ayon-sdd` tool lives in `<ROOT>/src`, not here (§3)
- [ ] Every in-scope repo has a correct, self-sufficient `AGENTS.md` with no dead
      `.ayon-main` reference. (C1)
- [ ] In the pilot repo (`ayon-batch-delivery`, §6 D4): `goose recipe list | grep -c
      speckit` = 10 and `goose skills list | grep -c speckit` = 10. (C2)
- [ ] All seven repos in the §6 D1 table are **still on their expected branch** and have
      the SDD artifacts committed there. No commit landed on `develop`/`main`, and no PR
      was opened to `ynput/*`. (C3, D1)
- [ ] `ayon-batch-delivery/.github/copilot-instructions.md` is **gone**, its unique
      content preserved in `AGENTS.md`. (C1, §6 D2)
- [ ] `uv run ayon-sdd doctor` exits 0 for all in-scope repos. (D5)
- [ ] `git -C <repo> status --porcelain` is clean despite the local symlinks. (D2)
- [ ] A new worktree — created **both** via `git worktree add` and via Zed's picker —
      comes up with `.agents-main` resolving and `.env` present. (D1, D4)
- [ ] `goose review` runs the AYON checks in the pilot repo. (B4)
- [ ] D3 has an explicit **verified / falsified** result recorded in this file.
- [ ] Phase F only started after A–E are green.

**Reproducibility (Phase G) — the plan is not done until all of these hold:**

- [ ] Every phase-A file in `~/.config/` is reproducible from
      `uv run ayon-sdd install-global`; none is a hand-written one-off. (A, G1)
- [ ] All the scripts in the G1 table exist under
      `<ROOT>/src/jeza_ynput_dev_workspace/`, are exported in `__init__.py`, and are
      registered in `<ROOT>/pyproject.toml` `[project.scripts]`. (G1)
- [ ] `grep -rn "/Users/jakub" <ROOT>/src` returns **nothing**. (§5 hard gate)
- [ ] Every mutating `ayon-sdd` subcommand supports `--dry-run` and is idempotent
      (running it twice is a no-op and exits 0). (D5)
- [ ] The git `post-checkout` hook and the Zed `create_worktree` task both shell out to
      `ayon-sdd worktree-setup` — no duplicated logic. (D1, D4, G1)
- [ ] `~/.config/zed/tasks.json` contains **"AYON / Bootstrap agentic workspace HERE"**
      and **"AYON / Doctor"**, and both appear when an arbitrary folder is opened in
      Zed. (G4)
- [ ] **The clean-folder proof (G5):** a fresh clone into an empty directory reaches a
      green `ayon-sdd doctor` with **zero manual steps**, and the §7 checks above hold
      inside it. Scratch folder deleted afterwards.
- [ ] `<ROOT>/README.md` documents the full G0(a) chain, `--all` vs default scope, both
      Zed task names, the `doctor` verification, the fresh-machine limitation and the
      prerequisites. (G6, §6 D5)

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
