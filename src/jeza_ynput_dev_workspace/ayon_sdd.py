#!/usr/bin/env python

"""Umbrella CLI for the AYON SDD workspace tooling.

Individual behaviours are implemented as their own modules (one per
subcommand, following the existing ``src/`` conventions) and attached here so
the whole toolchain is reachable as ``uv run ayon-sdd <subcommand>``. Phase A
wired up ``install-global``; Phase D adds ``link``, ``unlink``, ``status``
and ``worktree-setup``; Phase G adds ``init-speckit``, ``doctor`` and
``bootstrap`` -- the last of these lets a brand-new, empty workspace folder
reach the full A-F state with this one command. Each subcommand also stays
runnable as its own ``ayon-sdd-<name>`` entry point.
"""

import click

from .bootstrap_workspace import bootstrap
from .sdd_doctor import doctor
from .sdd_init_speckit import init_speckit
from .sdd_install_global import install_global
from .sdd_link import link, unlink
from .sdd_status import status
from .sdd_worktree_setup import worktree_setup


@click.group()
def ayon_sdd():
    """AYON SDD workspace tooling (see IMPLEMENTATION-PLAN.md)."""


ayon_sdd.add_command(install_global, name="install-global")
ayon_sdd.add_command(link, name="link")
ayon_sdd.add_command(unlink, name="unlink")
ayon_sdd.add_command(status, name="status")
ayon_sdd.add_command(worktree_setup, name="worktree-setup")
ayon_sdd.add_command(init_speckit, name="init-speckit")
ayon_sdd.add_command(doctor, name="doctor")
ayon_sdd.add_command(bootstrap, name="bootstrap")


if __name__ == "__main__":
    ayon_sdd()
