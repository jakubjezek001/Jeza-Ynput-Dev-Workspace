#!/usr/bin/env python

"""Umbrella CLI for the AYON SDD workspace tooling.

Individual behaviours are implemented as their own modules (one per
subcommand, following the existing ``src/`` conventions) and attached here so
the whole toolchain is reachable as ``uv run ayon-sdd <subcommand>``. Phase A
only wires up ``install-global``; later phases (link, unlink, status,
init-speckit, worktree-setup, doctor, bootstrap) add their subcommands here
without duplicating logic — each also stays runnable as its own
``ayon-sdd-<name>`` entry point.
"""

import click

from .sdd_install_global import install_global


@click.group()
def ayon_sdd():
    """AYON SDD workspace tooling (see IMPLEMENTATION-PLAN.md)."""


ayon_sdd.add_command(install_global, name="install-global")


if __name__ == "__main__":
    ayon_sdd()
