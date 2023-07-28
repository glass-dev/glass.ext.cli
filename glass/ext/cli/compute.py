# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Commands that compute and store data."""

import os.path
import click
from glass.user import save_cls
from glass.ext.config import (ConfigError, cls_from_config, cosmo_from_config,
                              shells_from_config)

from .config import pass_config


def compute_cls_method(config):
    """Return the method used for computing Cls.

    This will look at both 'fields.cls' and 'compute.cls' in the
    configuration, and return the more adequate choice.

    """
    method = config.getstr("fields.cls", None)
    if method is None or method == "load":
        try:
            method = config.getstr("compute.cls")
        except ConfigError as exc:
            if method is None:
                exc.add_note("You must configure 'compute.cls' "
                             "if 'fields.cls' is not set.")
            elif method == "load":
                exc.add_note("You must configure 'compute.cls' "
                             "if 'fields.cls' is set to 'load'.")
            raise
    return method


@click.group()
def cli():
    """Compute and store simulation files."""


@cli.command()
@click.option("-f", "--force", is_flag=True,
              help="Force writing over existing file.")
@pass_config
def cls(config, force):
    """Compute and store angular matter power spectra."""
    method = compute_cls_method(config)
    path = config.getstr("fields.cls.path", None)
    if path is None:
        try:
            path = config.getstr("compute.cls.path")
        except ConfigError as exc:
            exc.add_note("You must configure 'compute.cls.path' "
                         "if 'fields.cls.path' is not set.")
            raise
    echo_method = click.style(method, bold=True, underline=True)
    echo_path = click.style(path, bold=True, underline=True)
    click.echo(f"Writing '{echo_method}' Cls to '{echo_path}' ...")
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
