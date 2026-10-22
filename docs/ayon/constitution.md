# AYON addon constitution

> **Scope:** every change made to an AYON addon repository in this
> workspace — plans, code, reviews, commit messages and PR descriptions.
> When a plan conflicts with an article, the plan is wrong and must be
> changed. The file evidence behind each article is in
> [constitution-evidence.md](constitution-evidence.md). Every principle here
> must point to an existing file (see [Amendment process](#amendment-process)).

---

## Article 1 — Addon anatomy is fixed

All addon repos share one top-level shape, and no other shape is acceptable
for new addons:

- `client/<package>/` — the code loaded by the host application or launcher.
- `server/` — settings models and the addon's `ServerAddon` subclass
  (`server/addon.py`, `server/settings/`).
- `package.py` — a small declarative metadata module at repo root: `name`,
  `title`, `version`, `client_dir`, `ayon_server_version`,
  `ayon_required_addons`, `ayon_compatible_addons`; plus host-specific or
  service-specific fields where the addon actually needs them (e.g. `services`
  only where a farm-side service runs).
- `create_package.py` — a per-repo copy, never a shared script. Its contract:
  read `package.py`, write `client/<package>/version.py` from it, embed
  `server/` directly, and zip the client into `private/client.zip`. Never
  assume its internals import cleanly from another addon.

A new top-level directory outside this shape (e.g. `lib/` at repo root
instead of inside `client/<package>/`) needs an explicit, justified exception
— it is not the default.

## Article 2 — Pipeline contracts are functional, not cosmetic

These values are load-bearing identifiers consumed by AYON Core, Pyblish,
and the server; renaming or reshaping any of them is a behavioral change, not
a cosmetic one, and must be treated as such in plans and reviews:

- **Pyblish plugin `order`** — offsets are not decorative; they control
  collection/validation sequencing.
- **`hosts` and `families`/`productBaseType`** — these select which instances
  a plugin runs against; `productBaseType` is a cross-process contract
  between local publish and farm publish.
- **Creator/loader `identifier`** — persisted as instance/container metadata
  in the host's native scene/timeline representation; changing it orphans
  previously created instances.
- **`representations`** — produced by extractors, consumed by integrators and
  loaders; shape changes ripple into every loader.

A change touching any of the above must state the before/after value and
which other files (settings model, loader, farm skeleton) must change in
lockstep.

## Article 3 — Client settings and server settings are one contract

`server/settings/main.py` composes the addon's top-level `<Addon>Settings`
model from one module per concern. Binding rules:

- **Every list-of-named-items settings model validates uniqueness** via the
  shared `ensure_unique_names` validator. A new list-of-plugins setting
  without it is incomplete.
- **Plugin settings keys commonly equal the exact Python class name.**
  Renaming a plugin means updating: the server settings model key, the
  settings defaults, and any client code that reads that settings category.
  One-file renames of creator/loader/publish plugins do not exist in this
  codebase.
- **Client plugins read settings through the addon's own top-level category**
  (e.g. `["nuke"]`) — never through another addon's category, even for shared
  concepts like image I/O.
- Shared, non-addon-specific settings primitives (`Vector2d`, `Vector3d`,
  `Box`, `validate_json_dict`, color types) live in the addon's own
  `server/settings/common.py`; do not duplicate them ad hoc in the same addon.
- **Settings schema changes are versioned migrations.** When a feature or
  bugfix changes the structure or renames existing fields of a settings
  model, add a conversion to the addon's conversion module (e.g.
  `server/settings/conversion.py`; create the file if the repo has none) and
  chain it from the addon's `convert_settings_overrides`, which then
  delegates to the base. Conversions are defensive no-ops on absent keys and
  version-guarded where only a source-version range is affected. Renaming a
  field without a conversion orphans stored project overrides.

## Article 4 — Compatibility imports are not dead code

Addons declare minimum `ayon_server_version` / `ayon_required_addons` in
`package.py`. Modules that branch on AYON Core API location or version are
satisfying that declared compatibility range, not leftover cruft. Do not
"clean up" an import branch without checking whether the addon's declared
minimum core version still needs it.

## Article 5 — Ruff is the authoritative style

Repos enforce Ruff with `line-length = 79`, `indent-width = 4`,
`select = ["E", "F", "W"]`, and double-quoted strings. Beyond that, config is
repo-specific — notably `preview`, `pydocstyle.convention`, and
`per-file-ignores` differ per addon. **Read the target repo's own
`ruff.toml`; never port a rule from another addon's copy.**

## Article 6 — Vendored code is invisible to tooling

Never propose formatting or linting a `vendor/` tree. The Ruff exclude path
is repo-specific — a literal path in each addon's `ruff.toml`, not a shared
glob. **Read the target repo's own `ruff.toml` before touching anything that
sits under a vendor directory.**

## Article 7 — Host client code has a hard runtime boundary

Host-integration addons depend on the host's embedded Python API and cannot
be imported in a bare interpreter. In every host addon:

- The addon-registration module (e.g. `NukeAddon` in `addon.py`) configures
  host paths and env, must be importable at launcher time **before the host
  starts**, and must not import the host's API module itself.
- Host-API-dependent startup/GUI code (e.g. `startup/init.py`,
  `startup/menu.py`) runs only once the host is up; GUI/menu code must stay
  out of any path that can execute in a headless farm render process.
- The host integration seam (pipeline install/registration) is where the
  Pyblish host and plugin directories are registered, and it requires the
  live host module.

The exact layout differs per host (`nuke`, `flame`, `resolve`, `hiero`) —
check the target repo's own `client/` layout, do not port directory-name
assumptions between hosts.

## Article 8 — The verification ladder depends on what the repo has

The correct ladder, in order, stopping at the first inapplicable step:

1. `ruff check .`
2. `ruff format --check .`
3. If a `tests/` directory (or `testpaths` in `pyproject.toml`
   `[tool.pytest.ini_options]`) exists in the repo — run that test suite (or
   the repo's own wrapper). Do not add a test framework to a repo that has
   none; that is an explicit non-goal, not an oversight.
4. `python create_package.py --skip-zip` — packaging must succeed even
   without a host available.
5. Host-application validation: describe the manual reviewer steps a human
   must run; do not claim to have executed them from an agent session.

## Article 9 — Private repositories are non-referenceable

Any repository that cannot be verified as public is presumed private and
MUST NOT be named, used, quoted, adapted, or derived from anywhere in the
work produced — plans, code, comments, docs, commit messages, PR
descriptions, or review notes. This prohibition covers the repository's
name, owner, file paths, module/class/identifier names, architecture, and
behavior, as well as any code, settings, or conventions derived from it.

Content in private repositories may fall under Trusted Production Network
(TPN) security contracts or commercial licenses. Referencing or reusing it
without authorization is a security and licensing violation that MUST be
avoided even when the reference seems incidental (e.g. a "similar to X"
note or a copy-pasted settings key).

Before naming or relying on any repository outside the surveyed public set,
check its visibility with:

- `gh repo view <owner>/<repo> --json visibility`
  (or an equivalent GitHub API query).

Fail-closed behavior:

- If the check fails — not found, insufficient auth — treat the repo as
  private.
- If verification would require a private token or a workaround, that is
  itself a signal the repo is not callable: stop, do not proceed.
- Being a known partner/premium addon, or having a `.github` layout that
  looks public, does not override the visibility requirement.

Exception — development work done inside a private repository: when the
work product itself is created within that private repository (the
repository being developed, or its own sibling private repositories in the
same authorised scope), referencing, using, and deriving from its content is
permitted. The rule exists to prevent unauthorised disclosure of private or
commercially licensed content into public or third-party work, not to block
legitimate development that happens inside the private scope itself. The
protection still applies to the output: content from that private scope must
never be carried into public repositories, public artifacts, forks, or work
produced for other parties.

A need for a private surface must be flagged to the human as an open item in
the plan or PR description — never smuggled in silently. The human may grant
an explicit, documented, task-scoped exception; without it, absence from the
work product is the only compliant outcome.

## Article 10 — Stop when a feature already exists

Before starting work on a requested feature, survey the repository for an
existing feature matching the request. If one is found: stop immediately —
create no branch, files, or directories — report the existing feature, and
ask the user to choose: update the existing feature, or abandon the request.
Do not proceed until the user decides.

---

## Amendment process

This constitution is derived from evidence, not preference. Amending it means
either (a) a cited file changed and the article must be updated to match, or
(b) a surveyed repo exhibits a genuine, justified divergence that becomes a
documented exception (per Article 1). Do not add a principle that cannot be
pointed at an existing file in a surveyed repo. Amendments follow semantic
versioning (MAJOR: incompatible removal/redefinition; MINOR: new section or
materially expanded guidance; PATCH: clarification/wording). Record the
affected evidence in [constitution-evidence.md](constitution-evidence.md)
in the same change.

## Governance

- The constitution supersedes all other practices; conflicting plans must be
  amended, not the constitution bent to fit them.
- Plans and PRs reference (not restate) the articles they comply with.
- Compliance is verified in plan and code review, using
  [review-checks.md](review-checks.md).
- This document lives in this workspace repository
  (`docs/ayon/constitution.md`); there is no other copy.

---

**Version**: 3.0.0 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-10-22

History: 2.0.0 moved evidence to the annex; 2.1.0 added settings
migrations (Article 3); 2.2.0–2.3.0 added Article 9 and its private-repo
exception; 2.4.0 added Article 10; 3.0.0 moved the constitution into this
repository and widened its scope to every change.
