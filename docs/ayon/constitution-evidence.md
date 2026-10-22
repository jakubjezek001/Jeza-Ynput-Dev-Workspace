# AYON addon constitution — evidence annex

Companion to [constitution.md](constitution.md). Read this file only when
justifying an amendment or settling a conflict. It backs each article with
the files it was verified against; the amendment process requires every
principle to point at an existing file, and this annex is where those
citations live.

**Survey date:** 2026-09-02, across `ayon-core`, `ayon-nuke`,
`ayon-batch-delivery`. Re-verify paths and line numbers before citing; they
are evidence of record, not load-bearing guarantees.

---

## Article 1 — Addon anatomy

- `ayon-core/client/ayon_core/`, `ayon-nuke/client/ayon_nuke/`,
  `ayon-batch-delivery/client/ayon_batchdelivery/` (plus second shared
  package in batch-delivery: `client/batchdelivery_common/`).
- `package.py` differences: `ayon-batch-delivery/package.py` declares a
  `DeadlineSubmitter` service image; `ayon-nuke/package.py` sets
  `app_host_name = "nuke"` and `project_can_override_addon_version = True` —
  host-integration addons need these, pure server/service addons do not.
- Each repo has its own `create_package.py` (import order and helper naming
  differ), but all agree on the contract: read `package.py`, write
  `client/<package>/version.py` from it, embed `server/` directly, and zip
  the client into `private/client.zip`.

## Article 2 — Pipeline contracts

- Pyblish order:
  `ayon-batch-delivery/client/ayon_batchdelivery/plugins/publish/collect_offloaded_processing_context.py`
  sets `order = pyblish.api.CollectorOrder - 0.399`.
- `productBaseType` read/written throughout
  `ayon-core/client/ayon_core/pipeline/farm/pyblish_functions.py` (collected
  onto `instance.data`, propagated into the farm "skeleton" instance).
- Creator/loader identifier:
  `ayon-nuke/client/ayon_nuke/plugins/create/create_camera.py` sets
  `identifier = "create_camera"` (persisted as Nuke node AYON metadata).
- Representations consumed via `representation_matches`-style filtering:
  `ayon-batch-delivery/client/batchdelivery_common/publish.py`.

## Article 3 — Client ⇄ server settings

- Example composition (`ayon-nuke/server/settings/main.py`):
  `NukeSettings(BaseSettingsModel)` with
  `general: GeneralSettings = SettingsField(default_factory=GeneralSettings, ...)`.
- `ayon-nuke/server/settings/` concern modules (eleven): `general`, `imageio`,
  `dirmap`, `scriptsmenu`, `gizmo`, `create_plugins`, `publish_plugins`,
  `loader_plugins`, `workfile_builder`, `workfile_callbacks`,
  `templated_workfile_build`.
- `ayon-batch-delivery/server/settings/` concerns: `delivery`, `transcoding`,
  `publish_plugins`, `conversions`.
- `ensure_unique_names` verified in `ayon-nuke/server/settings/create_plugins.py`
  (line 88) and `server/settings/common.py`.

## Article 4 — Compatibility imports

- `ayon-nuke/package.py`: `ayon_server_version = ">=1.1.2"`, core >= 1.9.9.
- `ayon-batch-delivery/package.py`: core >= 1.4.0 plus five other required
  addons.

## Article 5 — Ruff

- Identical across `ayon-core/ruff.toml`, `ayon-nuke/ruff.toml`,
  `ayon-batch-delivery/ruff.toml`: `line-length = 79`, `indent-width = 4`,
  `[lint] select = ["E", "F", "W"]`, `ignore = []`, `fixable = ["ALL"]`,
  `dummy-variable-rgx` (underscore-prefixed unused vars only)
  `[format] quote-style = "double"`, `skip-magic-trailing-comma = false`.
- `ayon-core` and `ayon-batch-delivery` add `[lint] preview = true` and
  `pydocstyle.convention = "google"`, plus
  `[lint.per-file-ignores] "tests/*.py" = ["S101", "PLR2004"]`.
  `ayon-nuke` has neither `preview` nor a `tests/` override (no `tests/`
  directory — see Article 8 evidence).
- CI: `astral-sh/ruff-action@v3` with `version-file: "pyproject.toml"`
  (`ayon-core/.github/workflows/pr_linting.yml`); every surveyed repo runs an
  equivalent linting workflow on PRs to `develop`.
- `ayon-launcher` is a verified exception — no `ruff.toml`; uses `setup.cfg`
  `[flake8]` with `chartboost/ruff-action@v1`. Always read the repo's own
  lint config.

## Article 6 — Vendored code

- `ayon-nuke/ruff.toml`: top-level `exclude` includes the literal entry
  `"client/ayon_nuke/vendor"`.
- `ayon-batch-delivery/ruff.toml`: a second `exclude = [...]` block under
  `[lint]` lists `"client/ayon_batchdelivery/vendor/*"`, plus a stale
  per-file-ignore `"client/ayon_core/lib/__init__.py"` (copy-paste leftover
  from `ayon-core` pointing at nothing in that repo — flag if touched, never
  silently "fix" as part of an unrelated change).
- `ayon-core/ruff.toml`: generic name-based `"vendor"` exclude plus one
  specific file, `client/ayon_core/scripts/slates/__init__.py`.
- `ayon-launcher`: flake8 `exclude` includes `*/vendor`.

## Article 7 — Host runtime boundary

Verified on `ayon-nuke` (surveyed example):

- `client/ayon_nuke/addon.py` (`NukeAddon`) configures `NUKE_PATH` and
  `PYTHONPATH`, sets logging, removes env values that interfere with Nuke;
  must be importable at launcher time, before Nuke starts — must not import
  `nuke` itself.
- `client/ayon_nuke/startup/init.py` and `startup/menu.py` run once Nuke is
  up; `menu.py` is explicitly GUI-only and must stay out of any headless
  farm render path.
- `client/ayon_nuke/api/pipeline.py` (`NukeHost.install()`) registers the
  Pyblish host and create/load/inventory/workfile-build/publish plugin
  directories; it requires the live `nuke` module.

Host layouts differ ([repo-types/host-integration.md](repo-types/host-integration.md)
documents the four host-addon `client/` trees: nuke `api/ plugins/ startup/
vendor/`; flame `api/ plugins/ hooks/ otio/ scripts/ startup/`; resolve
`api/ plugins/ hooks/ otio/ presets/ utility_scripts/`; hiero
`api/ plugins/ vendor/`). Do not port directory-name assumptions across
hosts.

## Article 8 — Verification ladder evidence

- `ayon-core`: linting workflow
  (`.github/workflows/pr_linting.yml`, `ruff-action`) **and** real CI unit
  tests (`.github/workflows/pr_unittests.yaml`:
  `./tools/manage.sh create-env` → `./tools/manage.sh run-tests`;
  `testpaths = ["client/ayon_core/tests", "tests/client/ayon_core/ui"]`).
- `ayon-batch-delivery`: real `tests/` directory (`test_common_publish.py`,
  `test_api_helpers.py`, `test_delivery_and_ocio_helpers.py`) with a
  `conftest.py` that stubs `ayon_batchdelivery` onto `sys.path` from `client/`;
  no dedicated unit-test CI workflow.
- `ayon-nuke`: no `tests/`, no test workflow; its `AGENTS.md` states "There
  is no checked-in test suite. Nuke behavior requires validation in a
  compatible Nuke + AYON environment."

## Article 9 — Private repositories are non-referenceable

Policy rule, not derived from surveyed-repo evidence. Mandated by the owning
organisation (2026-09-11); rationale: private/partner repos may carry TPN
security contracts or commercial licenses, so naming or deriving from them
is a security and licensing violation even when the reference seems
incidental. Enforcement mechanism: `gh repo view <owner>/<repo>
--json visibility`, fail-closed on any check failure or workaround.
Exception (added 2026-09-11): development work done inside a private
repository may reference its own private scope, provided content never
leaks into public or third-party artifacts.

## Article 10 — Stop when a feature already exists

Workflow-policy rule, not derived from surveyed-repo evidence. Mandated
2026-09-11: survey first, and on a match stop before creating any branch,
file or directory, asking the user to choose between updating the existing
feature or abandoning the request.

---

## Maintaining this annex

Every amendment to the constitution records the affected evidence here in
the same change: which article's citation changed, the file and its
before/after state, and the survey date. Entries that can no longer be
pointed at an existing file are removed together with the principle they
supported.
