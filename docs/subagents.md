# Subagents

Subagents take bounded parts of a development task (find code, collect
impact facts, implement one piece, review a diff, write a PR description)
so the main session stays small and cheap. Their definitions never name a
model: they name a **tier**, and one small file maps tiers to models per
harness. They live in the harness-neutral `.agents/` folder; each harness
gets a generated copy in its own format ([the pieces](#the-pieces)). To
change cost, edit the tier map, not the definitions.

## Routing

Before any development work — a change in `src/`, `docs/` or an `ayon-*`
repo — split the task into parts and give each part to the cheapest worker
that can do it, in this order:

1. **A script**, when one exists: a workspace entry point
   ([workspace-tooling.md](workspace-tooling.md)) or the repo's own command
   (`ruff`, `create_package.py`). No model.
2. **You, the main session**: the plan, open points and questions to the
   user, files several parts share, commits, the PR. Also any change of one
   piece or a few files: a subagent costs a context of its own.
3. **A defined subagent** on its tier, for a part that is bounded,
   independent of the others and has a short answer (table below).

State the split in one line before you start, for example "`repo-scout` ×2
and `impact-scout` in parallel, then I implement; `diff-reviewer` before
the PR". Questions and read-only checks need no split.

| Work | Tier | By |
| --- | --- | --- |
| Where the change lives (the survey, Article 10), one question per place, in parallel | light | `repo-scout` |
| [Impact analysis](ayon/development-rules.md#impact-analysis-before-a-change) | light | `impact-scout` |
| Plan, open points, shared files, commits, PR title | — | you |
| One piece with its own files, when two or more pieces have disjoint files | standard | `change-implementer`, one per piece, in parallel |
| [Review checks](ayon/review-checks.md) before the PR | standard | `diff-reviewer` |
| PR title and description ([pull-requests.md](pull-requests.md)) | light | `pr-writer` |
| A merge or rebase stopped on conflicts | standard | `conflict-resolver` |
| A design the code and docs cannot settle | deep | one general-purpose agent on the model `uv run ayon-workspace agents tier deep` prints; say why |

Workspace tooling (`src/`, `docs/`, `.zed/`) is usually small enough to do
yourself; send `repo-scout` only when you do not know where to look.

## Picking a tier

Take the cheapest tier whose failure is cheap to notice and fix.

- **light**: the answer is found, not reasoned (search, extract, summarise
  given text, apply a fixed recipe). A wrong result is obvious from the
  output. The default for fan-out.
- **standard**: judgement on a bounded input (implement a scoped piece,
  review a diff, resolve a conflict, choose among a few options).
- **deep**: open-ended reasoning, design, debugging without a lead, or
  anything outward-facing or costly to redo. Rare; usually the main session
  itself, not a subagent.

When unsure, start one tier lower and move up only if the result needed
redoing; say so in the plan or the PR.

## Briefing and checking

- Give absolute paths: the workspace root, the checkout or worktree, the
  base ref, and for a writer the files it may change. Name the repo-type
  page ([development-rules.md](ayon/development-rules.md#pick-the-repo-type)).
- Cap the input (the question, the files, the facts it needs) and the
  output (each definition caps its reply).
- Fan out only independent parts, all in one message so they run in
  parallel. Two writers never touch the same file.
- Never pass a `model` to a defined subagent: its copy carries the tier's
  model.
- A subagent's report is a claim. Check `git -C <path> diff --stat` and run
  the repo's checks yourself before you build on it.
- Hand over no confidential content a part does not need (`__CLIENTS_WORK/`,
  private repositories;
  [Article 9](ayon/constitution.md#article-9--private-repositories-are-non-referenceable)).

## The pieces

Every subagent lives once, harness-neutral, in `.agents/`. No harness
reads subagents from a shared folder yet: each reads its own, in its own
format. So `.agents/` is the committed source, and
`uv run ayon-workspace agents sync` writes a copy for each harness, with
the model the tier gets there.

| What | Where |
| --- | --- |
| Definitions, the source | `.agents/agents/<name>.md`: frontmatter `name`, `description`, `tier`, `tools`, then the instructions |
| Tier → model and effort, per harness; which harnesses get copies | `.agents/tiers.json` (`harnesses`, `targets`; defaults in `workspace_agents.py`) |
| Harness copies, generated and gitignored | the folders below |

| Harness | Reads | Copy notes |
| --- | --- | --- |
| Claude Code | `.claude/agents/<name>.md` | model, effort and `tools` as given |
| Cursor | `.cursor/agents/<name>.md` | `readonly: true` when `tools` has no `Edit`/`Write` |
| Codex | `.codex/agents/<name>.toml` | instructions as `developer_instructions`, effort as `model_reasoning_effort` |
| Gemini CLI | `.gemini/agents/<name>.md` | tools inherited (its tool names differ) |
| OpenCode | `.opencode/agents/<name>.md` | `mode: subagent`, `permission: edit: deny` when read-only |
| VS Code / GitHub Copilot | `.github/agents/<name>.agent.md` | tools inherited |
| Pydantic AI harness, pi | `.agents/agents/` itself | no copy needed; the model is inherited |

A tier with no model in `.agents/tiers.json` inherits the delegating
session's model there; only Claude Code has models filled in, Codex has
efforts. Put a cheaper model on `light` for a harness you use to get the
saving there. Read-only definitions say so in their instructions too,
because not every harness enforces `tools` (Codex inherits the session's
sandbox).

A harness without file-defined subagents, or one not listed, still
follows the [routing](#routing): it reads `.agents/agents/<name>.md` and
hands the instructions, with the brief, to whatever delegation it has, or
does that part itself.

```bash
uv run ayon-workspace agents list          # each definition, its tier, its model per harness
uv run ayon-workspace agents tier deep     # one tier's model and effort per harness, as JSON
uv run ayon-workspace agents sync          # write every harness's copies
uv run ayon-workspace agents sync --check  # exit 1 if they drifted
```

`--harness NAME` limits any of them to one harness. The copies are not
committed ([agent-instructions.md](agent-instructions.md#layout)), so
each machine runs `sync` once; `bootstrap` does, and `doctor` reports
drift. After editing a definition or `.agents/tiers.json`, run `sync`.
Sessions find the copies when they are opened at the workspace root.

## Adding a harness

1. Write its copy format in `workspace_agents.py` (a `_render_<name>`
   function and its `HARNESSES` entry: folder, file name, writer).
2. Add it to `targets` and `harnesses` in `.agents/tiers.json`, with a
   model and effort per tier where it takes them.
3. Gitignore its folder, then `uv run ayon-workspace agents sync`.

`effort` is the harness's thinking or reasoning setting; a harness
without one leaves it out.

## Adding a subagent

A definition in `.agents/agents/` with a tier, `sync`, and a row in the
[routing](#routing) table. If a script can do the work, write the script
instead.
