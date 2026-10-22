# AYON development rules

Universal rules for working in any AYON addon repository in this workspace.
The binding version, with the reasoning behind each rule, is the
[constitution](constitution.md).

## Pick the repo type

Read the page that matches the repository you are working in:

- [repo-types/core.md](repo-types/core.md) — `ayon-core`.
- [repo-types/launcher.md](repo-types/launcher.md) — `ayon-launcher` (not an
  addon).
- [repo-types/host-integration.md](repo-types/host-integration.md) — host
  addons: `ayon-nuke`, `ayon-flame`, `ayon-resolve`, `ayon-hiero`,
  `ayon-maya`, `ayon-blender`, `ayon-fusion`, `ayon-slater`,
  `ayon-traypublisher`, `ayon-batch-delivery`, ...
- [repo-types/addon.md](repo-types/addon.md) — any other addon.

If the repository has its own `AGENTS.md`, read that too. It adds
repo-specific facts on top of these rules.

## Rules

- Reuse shared addon/API helpers for host operations, metadata, containers,
  workfiles, paths, and settings; do not invent parallel formats.
- Preserve pipeline contracts: identifiers, product types, families, hosts,
  orders, representations, and frame ranges (Article 2).
- Keep client settings paths aligned with server models and defaults. When
  renaming or adding configurable plugins, update all corresponding
  settings (Article 3).
- When changing settings schema or field names, convert stored overrides:
  add a `_convert_*` helper to the repo's settings conversion module
  (`server/settings/conversion.py`, or the repo's existing equivalent) and
  chain it through the addon's `convert_settings_overrides` so older stored
  overrides migrate. Never rename a settings field without a conversion.
- Preserve compatibility imports and runtime API handling required by the
  AYON Core and host versions this repo declares in `package.py`
  (Article 4).
- Keep vendor code excluded from formatting and linting (Article 6).
- Keep GUI-only code out of headless or farm startup paths (Article 7).
- Never mention or reuse content from repositories you have not verified as
  public. Check `gh repo view <owner>/<repo> --json visibility` first and
  fail closed (Article 9). Exception: when the repository being developed
  is itself private, its own private scope may be used, but must never leak
  into public or third-party artifacts.
- Before building a feature, survey the repo. If the feature already
  exists, stop and ask whether to update it or abandon the request
  (Article 10).
- Use Python 3.9+ unless the repository specifies otherwise.
- Do not add a new test framework to a repo that has none; validate with the
  narrowest relevant lint, build, or package command.

## Read the repo, not your memory

Each addon is configured independently; never assume paths or settings are
identical to another addon's. Before touching anything, check the target
repo's own:

- `ruff.toml` (or `[tool.ruff]` in `pyproject.toml`) — authoritative style;
  vendor excludes and `preview`/`per-file-ignores` differ per addon.
- `package.py` — declared `ayon_server_version` / `ayon_required_addons` /
  `ayon_compatible_addons`, before touching any compatibility-import branch.
- `server/settings/main.py` — how the top-level `<Addon>Settings` model is
  composed and the addon's settings category name (used by client code as
  `get_current_project_settings()["<category>"]`).
- `tests/` or `[tool.pytest.ini_options]` — whether this repo has a test
  suite at all.

## Impact analysis before a change

For any non-trivial change, answer these in the plan or PR description.
Answer only from what the change actually requires:

1. **Settings impact** (Article 3) — does it add, rename or remove a
   configurable plugin class? If yes, name the server settings model file
   and key that change with it, and the client settings-category lookup
   that must stay aligned. If no, say so.
2. **Host constraints** (Article 7) — does it run inside a host application
   with an import-time boundary, or is it host-agnostic?
3. **Pipeline contracts touched** (Article 2) — Pyblish `order`, `hosts`,
   `families`/`productBaseType`, creator/loader `identifier`: list the
   current and proposed value for each, or say none are touched.
4. **Addon anatomy** (Article 1) — does it stay inside `client/`/`server/`,
   or does it need a new top-level directory (which needs a justification)?

## Development checks (default ladder)

Run the repository's existing checks, typically:

```bash
ruff check .
ruff format --check .
# only if this repo has tests/ or [tool.pytest.ini_options]:
pytest
python create_package.py --skip-zip
```

Validation that needs the host application cannot run in an agent session;
describe the manual steps a reviewer must run instead. The repo-type pages
list the exact ladder per repo.

Before opening a PR, run the [review checks](review-checks.md). PR titles
and descriptions follow [pull-requests.md](../pull-requests.md).
