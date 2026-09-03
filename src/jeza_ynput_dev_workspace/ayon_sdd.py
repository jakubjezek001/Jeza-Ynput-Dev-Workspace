#!/usr/bin/env python

"""Umbrella CLI for the AYON SDD workspace tooling.

Individual behaviours are implemented as their own modules (one per
subcommand, following the existing ``src/`` conventions) and attached here so
the whole toolchain is reachable as ``uv run ayon-sdd <subcommand>``. Phase A
wired up ``install-global``; Phase D adds ``link``, ``unlink``, ``status``
and ``worktree-setup``; later phases (init-speckit, doctor, bootstrap) add
their subcommands here without duplicating logic — each also stays runnable
as its own ``ayon-sdd-<name>`` entry point.
"""

import click

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


if __name__ == "__main__":
    ayon_sdd()
