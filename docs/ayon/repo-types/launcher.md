# Repo type: `ayon-launcher`

`ayon-launcher` is **not** shaped like the addon repos (`ayon-core`,
`ayon-nuke`, `ayon-batch-delivery`). Do not apply the addon constitution's
`client/`/`server/`/`package.py` anatomy (Article 1) here — there is no
`server/` and no `package.py`; this repo builds the AYON desktop application
and its update/distribution logic, plus a native launcher binary.

## Layout (verified)

- `common/ayon_common/` — the actual Python payload, added to `sys.path` on
  bootstrap: `connection/` (server login/connection UI), `distribution/`
  (backend of addon/dependency-package distribution from the server),
  `startup/`, `resources/`. See `ARCHITECTURE.md` at repo root.
- `app_launcher.cpp` / `shim/` — native launcher components; do not expect
  Python tooling (ruff, pytest) to touch these.
- `vendor/` — third-party dependencies not on `PYTHONPATH`; excluded from
  linting the same way every other repo excludes its vendor tree.
- `tools/` — bash/PowerShell convenience scripts for common actions
  (`tools/*.sh`, `tools/*.ps1`).
- `build/`, `Dockerfile*`, `inno_setup.iss`, `setup.py` — packaging/build for
  the desktop app across platforms; out of scope for pipeline-content changes.

## Lint config is different here — verified, do not assume ruff.toml

This repo has **no `ruff.toml`**. Its CI linting step
(`.github/workflows/pr_linting.yml`) uses `chartboost/ruff-action@v1` with no
version-file pin (a different action version than `ayon-core`'s
`astral-sh/ruff-action@v3`). Local style is governed by `setup.cfg`
`[flake8]`:

```ini
[flake8]
ignore = BLK100, W504, W503
max-line-length = 79
exclude = .git, __pycache__, docs, */vendor, *deadline/repository/custom/plugins
max-complexity = 30
```

plus `[pydocstyle] convention = google, ignore = D107` and
`[pylint.'MESSAGES CONTROL'] disable = no-member`. Line length (79) matches
the addon convention, but the enforcement tool and ignore set do not — check
`setup.cfg` before assuming a rule from `ayon-core`/`ayon-nuke` applies.

## No `tests/` directory

There is no test suite in this repo (no `tests/` directory, no pytest config
in `pyproject.toml`). Validate changes by building/launching the app per
`ARCHITECTURE.md` and `tools/`, not by inventing a pytest suite.

## Verification ladder

```bash
flake8 .
python app_launcher.py   # or the platform build script under tools/
```
