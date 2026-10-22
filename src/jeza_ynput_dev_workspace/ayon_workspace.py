#!/usr/bin/env python

"""Umbrella CLI for the AYON workspace tooling.

Individual behaviours are implemented as their own modules (one per
subcommand, following the existing ``src/`` conventions) and attached here so
the whole toolchain is reachable as ``uv run ayon-workspace <subcommand>``.
``bootstrap`` brings a brand-new, empty workspace folder to a working state
with this one command. See docs/workspace-tooling.md.
"""

import click

from .bootstrap_workspace import bootstrap
from .workspace_doctor import doctor
from .workspace_install_global import install_global
from .workspace_link import link, unlink
from .workspace_status import status
from .workspace_worktree_setup import worktree_setup


@click.group()
def ayon_workspace():
    """AYON workspace tooling (see docs/workspace-tooling.md)."""


ayon_workspace.add_command(install_global, name="install-global")
ayon_workspace.add_command(link, name="link")
ayon_workspace.add_command(unlink, name="unlink")
ayon_workspace.add_command(status, name="status")
ayon_workspace.add_command(worktree_setup, name="worktree-setup")
ayon_workspace.add_command(doctor, name="doctor")
ayon_workspace.add_command(bootstrap, name="bootstrap")


if __name__ == "__main__":
    ayon_workspace()
