# Repo type: `ayon-core`

`ayon-core` is the shared pipeline library every host addon depends on
(`ayon_required_addons = {"core": ...}` in every other addon's `package.py`).
It is the one repo in scope with a real, CI-enforced unit-test suite —
treat it with more caution than a leaf addon: a behavior change here can
break every host integration at once.

## Layout (`client/ayon_core/`)

- `addon/` — `AYONAddon`/`ClickAddon` base classes and CLI wrapping
  (`addon/base.py`, `addon/click_wrap.py`, `addon/interfaces.py`).
- `host/` — the host abstraction: `host/host.py`, `host/abstract.py`,
  `host/interfaces/`, `host/dirmap.py`. Every host addon (`ayon-nuke`,
  `ayon-flame`, ...) implements against this.
- `pipeline/` — `create/`, `load/`, `publish/`, `workfile/`, `farm/`,
  `anatomy/`, `actions/`, `traits/`, `schema/`. `pipeline/farm/
  pyblish_functions.py` is where `productBaseType` and the farm "skeleton"
  instance are built — read this before changing anything that touches farm
  publishing (constitution Article 2).
- `settings/` — client-side settings access helpers (distinct from
  `server/settings/`, which defines the schema).
- `tests/` — real `pytest` suite; see verification ladder below.
- `vendor/` — excluded from Ruff (`ruff.toml` top-level `exclude` includes
  `"vendor"`); never propose linting/formatting it.

## Settings

`server/settings/` composes `ayon_core`'s top-level settings model the same
way `ayon-nuke` does (Article 3 of the constitution) — one module per
concern, `ensure_unique_names` on list-of-plugin settings, keys aligned to
exact class names.

## Verification ladder — this repo has a real CI unit-test gate

Unlike `ayon-nuke`/`ayon-batch-delivery`, `ayon-core` runs unit tests in CI
(`.github/workflows/pr_unittests.yaml`), not just linting:

```bash
ruff check .
ruff format --check .
./tools/manage.sh create-env   # installs the Qt/test env CI uses
./tools/manage.sh run-tests    # QT_QPA_PLATFORM=offscreen in CI
python create_package.py --skip-zip
```

`pyproject.toml [tool.pytest.ini_options]` scopes `testpaths` to
`client/ayon_core/tests` and `tests/client/ayon_core/ui`, and defines markers
`unit`, `integration`, `api`, `cli`, `slow`, `server` — use these to scope a
targeted run (`pytest -m unit`) instead of the full suite while iterating.

`ruff.toml` here additionally sets `[lint] preview = true` and
`pydocstyle.convention = "google"`, and excludes one specific file,
`client/ayon_core/scripts/slates/__init__.py`, in addition to the generic
`vendor` exclude — both are specific to this repo, do not assume they apply
elsewhere.
