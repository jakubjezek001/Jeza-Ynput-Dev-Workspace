# Repo type: generic addon

For any AYON addon repo not covered by a more specific page
([core.md](core.md), [launcher.md](launcher.md),
[host-integration.md](host-integration.md)). Read it together with
[the constitution](../constitution.md): this page is the short pointer, the
constitution holds the rules.

## What to check first, in this order

1. Does `ruff.toml` (or `[tool.ruff]` in `pyproject.toml`) exist? If yes, that
   file is authoritative for this repo — read it, do not assume it matches
   another addon's copy (Article 5/6 of the constitution: vendor-exclude paths
   and `preview`/`per-file-ignores` differ per repo).
2. Does `tests/` exist, or does `pyproject.toml` have
   `[tool.pytest.ini_options]`? If yes, that test suite is part of the
   verification ladder for this repo. If no, do not add one — describe manual
   validation instead (Article 8).
3. Read `package.py` at repo root for the addon's declared
   `ayon_server_version` / `ayon_required_addons` / `ayon_compatible_addons`
   before touching any compatibility-import branch (Article 4).
4. Read `server/settings/main.py` to see how the addon composes its top-level
   settings model from per-concern modules, and find the addon's settings
   category name (used by client code as
   `get_current_project_settings()["<category>"]`).

## Verification ladder (default, override per Article 8 if this repo differs)

```bash
ruff check .
ruff format --check .
# only if this repo has tests/ or [tool.pytest.ini_options]:
pytest
python create_package.py --skip-zip
```

## Non-goals

- Do not add a new test framework to a repo that has none.
- Do not invent a settings key that does not match the plugin's exact class
  name unless the repo demonstrably breaks that pattern elsewhere.
- Do not reformat or lint anything under a vendor directory.
