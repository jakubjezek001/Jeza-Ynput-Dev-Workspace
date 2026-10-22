# Subagents

Subagents take bounded parts of a development task (find code, collect
impact facts, implement one piece, review a diff, write a PR description)
so the main session stays small and cheap. Their definitions never name a
model: they name a **tier**, and one small file maps tiers to models. To
change cost or provider, edit that file, not the definitions.

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
- Never pass a `model` to a defined subagent: its definition carries the
  tier.
- A subagent's report is a claim. Check `git -C <path> diff --stat` and run
  the repo's checks yourself before you build on it.
- Hand over no confidential content a part does not need (`__CLIENTS_WORK/`,
  private repositories;
  [Article 9](ayon/constitution.md#article-9--private-repositories-are-non-referenceable)).

## The pieces

| What | Where |
| --- | --- |
| Definitions, provider-neutral | `config/agents/<name>.md`: frontmatter `name`, `description`, `tier`, `tools`, then the instructions |
| Tier → model and thinking effort, per provider | `config/agents.json` (`provider` is the active one; defaults in `workspace_agents.py`) |
| Harness files, generated and gitignored | `.claude/agents/<name>.md` (Claude Code), written by `uv run ayon-workspace agents sync` |

```bash
uv run ayon-workspace agents list          # each definition, its tier and model now
uv run ayon-workspace agents tier deep     # one tier's model and effort as JSON
uv run ayon-workspace agents sync          # write the harness files
uv run ayon-workspace agents sync --check  # exit 1 if they drifted
```

The harness files are not committed
([agent-instructions.md](agent-instructions.md#layout)), so each machine
runs `sync` once; `bootstrap` does, and `doctor` reports drift. After
editing a definition or `config/agents.json`, run `sync`. Sessions find
these subagents when they are opened at the workspace root.

## Switching provider

1. Add `providers.<name>` with a model and effort for each tier in
   `config/agents.json`, and set `provider`.
2. Teach `workspace_agents.py` where that provider reads agent files
   (`OUTPUT_DIRS`, `render_definition`). Until then `sync` stops with a
   message, and the definitions stay usable as plain prompts for any
   harness's general-purpose agent.
3. `uv run ayon-workspace agents sync`.

`effort` is the provider's thinking or reasoning setting; a provider
without one leaves it out.

## Adding a subagent

A definition in `config/agents/` with a tier, `sync`, and a row in the
[routing](#routing) table. If a script can do the work, write the script
instead.
