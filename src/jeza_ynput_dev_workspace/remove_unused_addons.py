#!/usr/bin/env python

"""Remove addon versions that no active bundle uses from ayon-docker.

The server loads every addon version found in ``<ROOT>/ayon-docker/addons``.
A version is unused when no active (non-archived) bundle pins it. Without
``--apply`` the command only lists what it would remove (dry run); with it
the folders are deleted and the server is restarted.

Run with ``--path`` inside an addon checkout (main checkout or worktree),
only that addon's versions are considered; any other path (e.g. the
workspace root) considers every addon. ``--addon`` names the addon directly.

Always kept whole:
- the addons in ``DEFAULT_KEEP_ADDONS`` and the ones given with ``--keep``,
- addons an active bundle has an enabled development path for but pins no
  version of.

An addon with no version left is removed as a whole folder.

It requires having a .env file with the following keys:
- 'AYON_SERVER_URL': AYON server URL
- 'AYON_API_KEY': AYON service user api key
"""

from __future__ import annotations

import contextlib
import logging
import os
import runpy
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path

import ayon_api
import click
import requests
from ayon_api import ServerAPI, get_server_api_connection
from dotenv import load_dotenv

from .workspace_common import resolve_workspace_root

load_dotenv()

# Addons in development that no bundle pins a version of yet.
DEFAULT_KEEP_ADDONS = ("sn4",)

BUNDLE_FLAGS = {
    "isProduction": "production",
    "isStaging": "staging",
    "isDev": "dev",
    "isProject": "project",
}


@dataclass
class RemovalPlan:
    """Folders to remove from the addons directory and what stays."""

    # Paths relative to the addons directory: "<addon>/<version>" or
    # "<addon>" when no version of the addon is left.
    entries: list[str] = field(default_factory=list)
    keep: dict[str, list[str]] = field(default_factory=dict)
    # Addons kept whole, with the reason.
    kept_addons: dict[str, str] = field(default_factory=dict)
    # "<addon>/<version>" pinned by an active bundle but not on disk.
    missing: list[str] = field(default_factory=list)


def _disk_versions(addons_dir: Path) -> dict[str, list[str]]:
    """Return the version folders of every addon in ``addons_dir``.

    Returns:
        dict[str, list[str]]: Sorted version folder names per addon.
    """
    versions = {}
    for addon_dir in sorted(addons_dir.iterdir()):
        if addon_dir.name.startswith(".") or not addon_dir.is_dir():
            continue
        versions[addon_dir.name] = sorted(
            version_dir.name
            for version_dir in addon_dir.iterdir()
            if not version_dir.name.startswith(".") and version_dir.is_dir()
        )
    return versions


def _folder_size(path: Path) -> int:
    """Return the size of all files under ``path`` in bytes.

    Returns:
        int: Sum of the file sizes.
    """
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            with contextlib.suppress(OSError):
                total += os.lstat(os.path.join(root, name)).st_size
    return total


def _format_size(size: float) -> str:
    """Format a byte count the way ``du -h`` does.

    Returns:
        str: The size with a ``B``, ``K``, ``M`` or ``G`` suffix.
    """
    for unit in ("B", "K", "M", "G"):
        if size < 1024 or unit == "G":  # noqa: PLR2004
            break
        size /= 1024
    return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"


def _collect_bundle_addons(
    bundles: list[dict],
) -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    """Collect what the active bundles use.

    Returns:
        tuple[dict[str, set[str]], dict[str, list[str]]]: Pinned versions
        per addon, and the bundles with an enabled dev path per addon.
    """
    pinned: dict[str, set[str]] = {}
    dev_paths: dict[str, list[str]] = {}
    for bundle in bundles:
        if bundle.get("isArchived"):
            continue
        for name, version in (bundle.get("addons") or {}).items():
            if version:
                pinned.setdefault(name, set()).add(version)
        for name, dev in (bundle.get("addonDevelopment") or {}).items():
            if dev.get("enabled") and dev.get("path"):
                dev_paths.setdefault(name, []).append(bundle["name"])
    return pinned, dev_paths


def plan_removal(
    bundles: list[dict],
    disk: dict[str, list[str]],
    keep_names: set[str],
    scope: str | None = None,
) -> RemovalPlan:
    """Decide which addon version folders no active bundle uses.

    Args:
        bundles: Server bundles; archived ones are ignored.
        disk: Version folders per addon, from ``_disk_versions``.
        keep_names: Addons to keep whole.
        scope: Only consider this addon; ``None`` considers every addon.

    Returns:
        RemovalPlan: The folders to remove and what stays.
    """
    pinned, dev_paths = _collect_bundle_addons(bundles)
    plan = RemovalPlan()
    for name, versions in disk.items():
        if scope and name != scope:
            continue
        if name in keep_names:
            plan.kept_addons[name] = "keep list"
        elif name not in pinned and name in dev_paths:
            plan.kept_addons[name] = "dev path in " + ", ".join(
                dev_paths[name]
            )
        if name in plan.kept_addons:
            plan.keep[name] = versions
            continue

        used = [v for v in versions if v in pinned.get(name, set())]
        unused = [v for v in versions if v not in pinned.get(name, set())]
        if used:
            plan.keep[name] = used
            plan.entries += [f"{name}/{v}" for v in unused]
        elif unused:
            plan.entries.append(name)

    plan.missing = sorted(
        f"{name}/{version}"
        for name, versions in pinned.items()
        for version in versions
        if (not scope or name == scope) and version not in disk.get(name, [])
    )
    return plan


def _checkout_root(path: Path) -> Path | None:
    """Return the root of the git checkout or worktree containing ``path``.

    Returns:
        Path | None: The checkout root, or ``None`` outside git.
    """
    path = path.expanduser().resolve()
    search_dir = path if path.is_dir() else path.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(search_dir), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return Path(result.stdout.strip())


def _read_addon_name(checkout_root: Path) -> str | None:
    """Read the server addon name from the checkout's ``package.py``.

    The addons directory is keyed by the server addon name (e.g.
    ``"core"``), not by the repository name (e.g. ``"ayon-core"``).

    Returns:
        str | None: The addon name, or ``None`` without a ``package.py``.
    """
    package_file = checkout_root / "package.py"
    if not package_file.is_file():
        return None
    return runpy.run_path(str(package_file)).get("name") or None


def _resolve_scope(addon_name: str | None, path: Path) -> str | None:
    """Resolve which addon to clean and print the scope.

    ``addon_name`` wins; otherwise the server addon name comes from the
    ``package.py`` of the checkout containing ``path``.

    Returns:
        str | None: The server addon name, or ``None`` for every addon.
    """
    if addon_name:
        click.echo(f"Scope: addon '{addon_name}'")
        return addon_name
    checkout_root = _checkout_root(path)
    scope = _read_addon_name(checkout_root) if checkout_root else None
    if scope is None:
        click.echo("Scope: all addons")
        return None
    click.echo(f"Scope: addon '{scope}' (checkout {checkout_root})")
    return scope


def _describe_bundle(bundle: dict) -> str:
    flags = [label for key, label in BUNDLE_FLAGS.items() if bundle.get(key)]
    if not flags:
        return bundle["name"]
    return f"{bundle['name']} ({', '.join(flags)})"


def _connect(log: logging.Logger) -> tuple[ServerAPI, list[dict]]:
    """Log in to the server and fetch its active bundles.

    Returns:
        tuple[ServerAPI, list[dict]]: The connection and the active bundles.
    """
    try:
        ayon_api.init_service()
    except Exception as e:  # noqa: BLE001
        log.error(f"Failed to initialize AYON API: {e}")
        log.error(
            "Please check your AYON_SERVER_URL and AYON_API_KEY in .env file"
        )
        sys.exit(1)
    server = get_server_api_connection()
    bundles = [
        bundle
        for bundle in server.get_bundles()["bundles"]
        if not bundle.get("isArchived")
    ]
    if not bundles:
        log.error("No active bundles on the server, refusing to clean up")
        sys.exit(1)
    click.echo(
        "Active bundles: " + ", ".join(_describe_bundle(b) for b in bundles)
    )
    return server, bundles


def _print_plan(
    plan: RemovalPlan,
    addons_dir: Path,
    log: logging.Logger,
    *,
    apply_changes: bool,
) -> None:
    """Print the kept addons, warnings and the folders to remove."""
    for name, reason in plan.kept_addons.items():
        click.echo(f"Kept whole: {name} ({reason})")
    for missing in plan.missing:
        log.warning(f"Active bundle version not on disk: {missing}")
    if not plan.entries:
        click.echo("Nothing to remove.")
        return

    total = 0
    action = "remove" if apply_changes else "would remove"
    for entry in plan.entries:
        size = _folder_size(addons_dir / entry)
        total += size
        click.echo(f"{action}: {entry:<45} {_format_size(size):>6}")
    click.echo(f"{len(plan.entries)} folders, {_format_size(total)}")


def _wait_for_server_restart(
    server_url: str,
    log: logging.Logger,
    down_timeout: float = 15.0,
    up_timeout: float = 90.0,
    interval: float = 1.0,
) -> bool:
    """Wait until the server went down after restart and is up again.

    The restart request returns before the server actually shuts down, so
    waiting only for the server to respond could pass on the old process.
    If the down state is never observed (fast restart), continue anyway.

    Returns:
        bool: ``True`` when the server responds again within ``up_timeout``.
    """
    info_url = f"{server_url.rstrip('/')}/api/info"

    def is_up() -> bool:
        try:
            response = requests.get(info_url, timeout=2)
        except requests.RequestException:
            return False
        return response.status_code == HTTPStatus.OK

    deadline = time.monotonic() + down_timeout
    while time.monotonic() < deadline:
        if not is_up():
            log.debug("Server is down, waiting for it to come back")
            break
        time.sleep(interval)
    else:
        log.debug("Server restart was not observed, continuing")

    deadline = time.monotonic() + up_timeout
    while time.monotonic() < deadline:
        if is_up():
            return True
        time.sleep(interval)
    return False


def _wait_for_server_addons(
    server: ServerAPI,
    addons_dir: Path,
    scope: str | None,
    timeout: float = 60.0,
    interval: float = 2.0,
) -> tuple[list[str], list[str]]:
    """Wait until the server lists no version that is gone from disk.

    Returns:
        tuple[list[str], list[str]]: ``(only_on_server, only_on_disk)``
        version paths once the server dropped the removed versions, or
        what is left of them at ``timeout``.
    """
    deadline = time.monotonic() + timeout
    while True:
        disk = {
            name: set(versions)
            for name, versions in _disk_versions(addons_dir).items()
            if versions and (not scope or name == scope)
        }
        try:
            addons = server.get_addons_info(details=False)["addons"]
        except (requests.RequestException, ayon_api.exceptions.ServerError):
            addons = None
        if addons is not None:
            on_server = {
                addon["name"]: set(addon["versions"])
                for addon in addons
                if not scope or addon["name"] == scope
            }
            only_on_server = sorted(
                f"{name}/{version}"
                for name, versions in on_server.items()
                for version in versions - disk.get(name, set())
            )
            only_on_disk = sorted(
                f"{name}/{version}"
                for name, versions in disk.items()
                for version in versions - on_server.get(name, set())
            )
            if not only_on_server or time.monotonic() >= deadline:
                return only_on_server, only_on_disk
        elif time.monotonic() >= deadline:
            return ["<server addon list not available>"], []
        time.sleep(interval)


def _restart_and_verify(
    server: ServerAPI,
    addons_dir: Path,
    scope: str | None,
    log: logging.Logger,
) -> None:
    """Restart the server and check it lists the versions left on disk."""
    try:
        server.trigger_server_restart()
    except Exception as e:  # noqa: BLE001
        log.error(f"Failed to restart server: {e}")
        sys.exit(1)
    click.echo("Server restart triggered, waiting for it to come back")
    if not _wait_for_server_restart(os.environ["AYON_SERVER_URL"], log):
        log.error("Server did not come back after restart")
        sys.exit(1)

    only_on_server, only_on_disk = _wait_for_server_addons(
        server, addons_dir, scope
    )
    for version in only_on_server:
        log.error(f"Server still lists a removed version: {version}")
    for version in only_on_disk:
        log.warning(f"Server did not load the folder: {version}")
    if only_on_server:
        sys.exit(1)
    click.echo("Server lists exactly the addon versions left on disk.")


@click.command()
@click.option("--debug", is_flag=True, help="Debug log messages.")
@click.option(
    "-p",
    "--path",
    "path",
    default=".",
    show_default=True,
    help=(
        "Path inside an addon checkout limits the cleanup to that addon; "
        "any other path cleans every addon."
    ),
)
@click.option(
    "--addon",
    "addon_name",
    default=None,
    help="Server addon name to clean (e.g. 'nuke'), overrides --path.",
)
@click.option(
    "--keep",
    "keep",
    multiple=True,
    help=(
        "Addon to keep whole, repeatable. Always kept: "
        f"{', '.join(DEFAULT_KEEP_ADDONS)}."
    ),
)
@click.option(
    "--apply",
    "apply_changes",
    is_flag=True,
    help="Delete the folders and restart the server (default: dry run).",
)
@click.option("-y", "--yes", is_flag=True, help="Do not ask before deleting.")
@click.option(
    "--no-restart",
    is_flag=True,
    help="Do not restart the server after deleting.",
)
def remove_unused_addons(  # noqa: PLR0913, PLR0917
    debug: bool,  # noqa: FBT001
    path: str,
    addon_name: str | None,
    keep: tuple[str, ...],
    apply_changes: bool,  # noqa: FBT001
    yes: bool,  # noqa: FBT001
    no_restart: bool,  # noqa: FBT001
) -> None:
    """Remove addon versions that no active bundle uses (dry run default)."""
    # Set Log Level and create log object
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    log: logging.Logger = logging.getLogger("remove_unused_addons")

    # Validate required environment variables
    required_env_vars = ["AYON_SERVER_URL", "AYON_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        log.error(
            "Missing required environment variables: "
            f"{', '.join(missing_vars)}"
        )
        log.error("Please ensure these are set in your .env file")
        sys.exit(1)

    workspace_dir = resolve_workspace_root()
    addons_dir = workspace_dir / "ayon-docker" / "addons"
    if not addons_dir.is_dir():
        log.error(f"Docker addons directory not found: {addons_dir}")
        sys.exit(1)

    scope = _resolve_scope(addon_name, Path(path))
    server, bundles = _connect(log)
    disk = _disk_versions(addons_dir)
    if scope and scope not in disk:
        click.echo(f"No folders of addon '{scope}' in {addons_dir}")
        return

    plan = plan_removal(
        bundles, disk, set(DEFAULT_KEEP_ADDONS) | set(keep), scope
    )
    _print_plan(plan, addons_dir, log, apply_changes=apply_changes)
    if not plan.entries:
        return
    if not apply_changes:
        click.echo(
            "Dry run only. Run with --apply to delete and restart the server."
        )
        return

    if not yes:
        click.confirm(f"Delete {len(plan.entries)} folders?", abort=True)
    for entry in plan.entries:
        shutil.rmtree(addons_dir / entry)
        click.echo(f"removed: {entry}")

    if no_restart:
        click.echo("Server not restarted (--no-restart).")
        return
    _restart_and_verify(server, addons_dir, scope, log)
