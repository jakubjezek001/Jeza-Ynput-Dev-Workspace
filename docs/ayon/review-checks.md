# AYON review checks

Scoped checks for reviewing a diff or a plan in an AYON addon repo against
the [constitution](constitution.md). The same checks apply to a plan before
any code is written.

## How to run a scoped review

1. Identify the repo and its type
   ([development-rules.md](development-rules.md#pick-the-repo-type)).
2. Run each check below against the diff or plan under review.
3. Report failures grouped by check, each with a `file:line` reference and
   the article it violates. Do not report a finding you cannot trace to a
   specific article or repo-type statement.
4. A clean review reports all six checks as pass; it does not repeat the
   constitution's reasoning, only confirms compliance.

**Scope:** addon repos (`ayon-core`, `ayon-nuke`, `ayon-batch-delivery`,
`ayon-flame`, `ayon-resolve`, `ayon-hiero`, ...). For `ayon-launcher`, only
"Ruff conformance" and "Verification ladder" apply, both read through
[repo-types/launcher.md](repo-types/launcher.md) (no `ruff.toml`, no
`tests/`). The other four assume an addon anatomy that repo does not have.

| Check | Article |
| --- | --- |
| [Addon anatomy](#addon-anatomy) | 1 |
| [Pyblish contracts](#pyblish-contracts) | 2 |
| [Settings alignment](#settings-alignment) | 3 |
| [Ruff conformance](#ruff-conformance) | 5 |
| [Vendor exclusion](#vendor-exclusion) | 6 |
| [Verification ladder](#verification-ladder) | 8 |

## Addon anatomy

Fails if a change:

- Adds a top-level directory outside `client/<package>/`, `server/`,
  `package.py`, `create_package.py`, `docs/` without an explicit, stated
  justification for the exception.
- Adds or edits `package.py` without keeping `name`, `title`, `version`,
  `client_dir`, `ayon_server_version`, `ayon_required_addons`,
  `ayon_compatible_addons` present and consistent with the addon's actual
  role (host-integration addons carry `app_host_name`; service-shipping
  addons carry `services`; neither is required on every addon).
- Assumes `create_package.py` is a shared script importable across repos —
  it is a per-repo copy; changes to one repo's copy do not need to (and
  should not silently) mirror another repo's copy.

Pass: directory additions and `package.py` fields match the shape in
`ayon-core`, `ayon-nuke`, or `ayon-batch-delivery`, or the divergence is
explicitly justified in the PR or plan.

## Pyblish contracts

Fails if a change:

- Modifies a Pyblish plugin's `order`, `hosts`, or `families` value without
  stating why the new value is correct relative to other plugins in the same
  stage (collectors relative to other collectors, etc.).
- Renames or reshapes `productBaseType`, `families`, or `representations` on
  `instance.data` without updating every reader of that key — check
  `pipeline/farm/pyblish_functions.py`-style farm skeleton code, loaders that
  filter by representation, and any settings that reference the old family
  name.
- Changes a creator/loader `identifier` string without acknowledging that
  previously created instances/containers (stored as node/clip metadata)
  will no longer match, and without a stated migration or
  backward-compatibility path.

Pass: every changed contract value has an explicit before/after statement
and a list of the other files updated in lockstep.

## Settings alignment

Fails if a change:

- Adds a list-of-named-items settings field without a matching
  `ensure_unique_names` validator (reference implementation:
  `server/settings/create_plugins.py`).
- Adds or renames a configurable plugin class without updating the matching
  server settings model key, its default structure, and any client lookup of
  that settings path.
- Renames or restructures a settings field without a conversion chained
  through `convert_settings_overrides`.
- Has client code read a settings category other than this addon's own
  top-level category (e.g. `"nuke"` for `ayon-nuke`), or hardcode a value
  that a settings model already exposes.
- Duplicates a shared, non-addon-specific settings primitive (`Vector2d`,
  `Vector3d`, `Box`, color types, `validate_json_dict`-style helpers) instead
  of reusing what already exists in that repo's `server/settings/common.py`.

Pass: every new or renamed configurable plugin has a corresponding,
uniquely-validated server settings entry, and every client settings read
targets this addon's own category.

## Ruff conformance

Fails if a change:

- Introduces code that violates the repo's own `ruff.toml` — 79-character
  lines, 4-space indent, double-quoted strings, `E`/`F`/`W` selected with an
  empty `ignore` list, magic trailing commas respected.
- Assumes `[lint] preview = true` / `pydocstyle.convention = "google"` /
  `[lint.per-file-ignores] "tests/*.py" = [...]` apply, without checking
  whether *this* repo's `ruff.toml` actually sets them (`ayon-core` and
  `ayon-batch-delivery` do; `ayon-nuke` does not, and has no `tests/`
  override because it has no `tests/`).
- Assumes `ayon-launcher` has a `ruff.toml` at all — it does not; that repo
  is governed by `setup.cfg [flake8]` instead. Do not run or propose `ruff`
  config changes there.

Pass: `ruff check .` and `ruff format --check .` pass in the target repo
using that repo's own config file, and no rule from a different repo's
`ruff.toml` was assumed without verification.

## Vendor exclusion

Fails if a change:

- Proposes running `ruff check`, `ruff format`, or any linter/formatter fix
  against a path under a vendor directory (`client/<package>/vendor/` in
  `ayon-nuke`, `ayon-batch-delivery`, `ayon-hiero`; `vendor/` at repo root in
  `ayon-core` and `ayon-launcher`).
- Assumes the vendor-exclude glob is identical across repos. It is not; see
  [constitution-evidence.md](constitution-evidence.md#article-6--vendored-code)
  for each repo's exact entry (including the stray
  `client/ayon_core/lib/__init__.py` entry in `ayon-batch-delivery` — flag
  it, do not silently remove it as part of an unrelated change).
- Edits vendored code at all, for any reason other than a documented,
  upstream-tracked security or compatibility patch.

Pass: no diff touches a path under a vendor directory, and no new
lint/format automation is proposed for one.

## Verification ladder

Fails if the proposed validation:

- Runs `pytest` (or claims a test suite exists) in a repo with no `tests/`
  directory and no `[tool.pytest.ini_options]` (e.g. `ayon-nuke`,
  `ayon-launcher`) — instead it must describe manual host-application
  validation.
- Skips the local test suite in a repo that has one (`ayon-batch-delivery`'s
  `tests/`, `ayon-core`'s `client/ayon_core/tests` +
  `tests/client/ayon_core/ui`) because that repo has no CI unit-test
  workflow — "no CI gate" does not mean "skip it locally".
- Proposes adding a new test framework to a repo that intentionally has none.
- Claims to have executed Nuke/Flame/Resolve/Hiero/desktop-launcher steps
  from an agent session — those must be described as manual steps for a
  human reviewer, never claimed as executed.
- Skips `python create_package.py --skip-zip` (or the addon's packaging
  equivalent) for a repo that has `package.py` and `create_package.py`.

Pass: the validation steps match what is actually present in the target
repo, in the order: lint → format-check → tests (if present) → package (if
applicable) → manual host validation (if applicable).

---

## Audit procedures

Two mechanical audits that back the checks above. They are cheap and need
little judgement, so they suit a smaller or local model if your agent can
delegate. Neither writes files.

### Packaging validation (Articles 1, 8)

Never run this against `ayon-launcher` (no `package.py`, not an addon).

1. Confirm `package.py` exists at repo root with `name`, `title`, `version`,
   `client_dir`, `ayon_server_version`, `ayon_required_addons`,
   `ayon_compatible_addons`, and that role-specific fields (`app_host_name`,
   `project_can_override_addon_version`, `services`) match the addon's role.
2. Run `ruff check .` and `ruff format --check .` (skip if the repo has no
   `ruff.toml`). Report these separately from packaging failures.
3. If `tests/` exists, run the repo's own test command.
4. Run `python create_package.py --skip-zip` from repo root. Report the
   exact command output; do not summarize away an error. Only drop
   `--skip-zip` when the task needs the zip.
5. Confirm `client/<client_dir>/version.py` now matches `package.py`'s
   `version`, and that `server/` content and the packaged client were
   produced.

### Settings audit (Article 3)

1. Find `server/settings/main.py` and list every settings module it composes
   into the top-level `<Addon>Settings` model.
2. For each list-of-named-items field, confirm a matching
   `ensure_unique_names` validator exists in that module.
3. Grep the client code for `get_current_project_settings()[...]` (or
   equivalent) and confirm the category key is this addon's own.
4. For every configurable-looking plugin class (creators, loaders, publish
   plugins), confirm a settings entry whose key matches the exact class
   name, or state which plugins are intentionally not configurable.
5. Report drift as `<file>:<line> — <what> — expected <server model path> —
   found <client usage>`. Shared primitives in `server/settings/common.py`
   (`Vector2d`, `Vector3d`, `Box`, color types) are not per-plugin settings;
   do not report them.

This is an audit, not a design review: report misalignment against what the
server model already declares; do not propose settings redesigns.
