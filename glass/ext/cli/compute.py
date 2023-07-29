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

    This will first look at 'compute.cls' in the configuration, and fall
    back to 'fields.cls' if possible.

    """
    try:
        method = config.getstr("compute.cls")
    except ConfigError as exc:
        method = config.getstr("fields.cls", None)
        if method is None:
            exc.add_note("You must configure 'compute.cls' "
                         "if 'fields.cls' is not set.")
            raise
        elif method == "load":
            exc.add_note("You must configure 'compute.cls' "
                         "if 'fields.cls' is set to 'load'.")
            raise
        else:
            pass
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
    try:
        path = config.getstr("compute.cls.path")
    except ConfigError as exc:
        path = config.getstr("fields.cls.path", None)
        if path is None:
            exc.add_note("You must configure 'compute.cls.path' "
                         "if 'fields.cls.path' is not set.")
            raise
        else:
            pass
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


@cli.command()
@pass_config
@click.option("-f", "--force", is_flag=True,
              help="Force writing over existing file.")
def lensing_cls(config, force):
    """Compute lensing spectra for plotting."""
    import numpy as np
    from glass.shells import RadialWindow
    from ._plot import nearest_shell
    method = compute_cls_method(config)
    path = config.getstr("plot.lensing.cls")
    echo_method = click.style(method, bold=True, underline=True)
    echo_path = click.style(path, bold=True, underline=True)
    click.echo(f"Writing '{echo_method}' lensing Cls to '{echo_path}' ...")
    if os.path.exists(path) and not force:
        raise click.ClickException(f"File '{path}' exists "
                                   "(use --force to overwrite)")
    config["fields.cls"] = method
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    redshifts = config.getarray(float, "plot.lensing.redshifts")
    norms = []
    kerns = []
    for i in nearest_shell(redshifts, shells):
        zsrc = shells[i].zeff
        z = np.linspace(0, zsrc, 1000)
        w = (3*cosmo.omega_m/2*cosmo.xm(z)/cosmo.xm(zsrc)
             * cosmo.xm(z, zsrc)*(1 + z)/cosmo.ef(z))
        n = np.trapz(w, z)
        w /= n
        norms += [n]
        kerns += [RadialWindow(za=z, wa=w, zeff=zsrc)]
    cls = cls_from_config(config, kerns, cosmo)
    icls = iter(cls)
    n = len(norms)
    cls = [norms[i]*norms[j]*next(icls)
           for i in range(n) for j in range(i, -1, -1)]
    save_cls(path, cls)


if __name__ == "__main__":
    cli()
