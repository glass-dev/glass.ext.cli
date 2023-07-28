# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Commands that compute and store data."""

import os.path
import click
from glass.user import save_cls
from glass.ext.config import (cls_from_config, cosmo_from_config,
                              shells_from_config)

from .config import pass_config


@click.group()
def cli():
    """Compute and store simulation files."""


@cli.command()
@click.option("-f", "--force", is_flag=True,
              help="Force writing over existing file.")
@click.argument("method")
@click.argument("path", type=click.Path(writable=True))
@pass_config
def cls(config, method, path, force):
    """Compute and store angular matter power spectra."""
    if os.path.exists(path) and not force:
        raise click.ClickException(f"File '{path}' exists "
                                   "(use --force to overwrite)")
    config["fields.cls"] = method
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    cls = cls_from_config(config, shells, cosmo)
    save_cls(path, cls)


if __name__ == "__main__":
    cli()
