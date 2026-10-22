# Repo type: host-integration addons

Surveyed on `ayon-nuke`, `ayon-flame`, `ayon-resolve` and `ayon-hiero`;
the same pattern applies to the other host addons (`ayon-maya`,
`ayon-blender`, `ayon-fusion`, ...), but check their layout first.

Shared pattern verified across `client/` in all four repos: every one has an
`api/` package (the host integration layer) and a `plugins/` package
(create/load/publish plugins). Beyond that, each host has its own extra
directories reflecting its host API — do not assume they are identical:

- `ayon-nuke/client/ayon_nuke/`: `api/`, `plugins/`, `startup/`, `vendor/`.
- `ayon-flame/client/ayon_flame/`: `api/`, `plugins/`, `hooks/`, `otio/`,
  `scripts/`, `startup/` — no `vendor/`.
- `ayon-resolve/client/ayon_resolve/`: `api/`, `plugins/`, `hooks/`, `otio/`,
  `presets/`, `utility_scripts/` — no `startup/`, no `vendor/`.
- `ayon-hiero/client/ayon_hiero/`: `api/`, `plugins/`, `vendor/` — no
  `hooks/`, no `startup/`.

Do not port a directory-name assumption from `ayon-nuke` (e.g. `startup/`)
into `ayon-resolve` or `ayon-hiero` without checking that repo's own
`client/` layout first.

## The one contract that does hold everywhere: the runtime boundary

Every host addon's `api/` package is the seam between launcher-safe code and
host-API-dependent code (constitution Article 7). The addon-registration
module (e.g. `NukeAddon` in `ayon-nuke/client/ayon_nuke/addon.py`) must stay
importable without the host's Python API — it runs at launcher/hook time.
Code that calls into the host's own API (Nuke's `nuke` module, Resolve's
scripting API, Hiero's `hiero` module, Flame's `flame` module) lives inside
`api/` or `startup/`/`hooks/` and cannot be imported or exercised from a plain
interpreter or in a headless farm process if it also touches GUI/menu state.

## Creator/loader identifiers and node/clip metadata

Per constitution Article 2, creator and loader `identifier` strings
(e.g. `ayon-nuke/client/ayon_nuke/plugins/create/create_camera.py`:
`identifier = "create_camera"`) are persisted as instance/container metadata
in the host's native scene/timeline representation (Nuke node knobs, Resolve
timeline markers/metadata, Hiero tags, Flame clip metadata — verify the exact
mechanism in the target repo's `api/lib.py` or equivalent before assuming
Nuke's knob-based model transfers directly). Use the host's existing
`api`-level helpers for reading/writing this metadata; do not invent a new
metadata channel.

## Verification ladder

Same base ladder as [addon.md](addon.md) (`ruff check .` /
`ruff format --check .` / `python create_package.py --skip-zip`), plus:
manual validation inside the actual host application — describe the steps a
human reviewer must run there; an agent session cannot execute Nuke, Flame,
Resolve, or Hiero itself.
