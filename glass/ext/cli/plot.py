# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Commands for making various plots."""

import click

from .config import pass_config


@click.group()
def cli():
    """Generate various diagnostic plots."""


@cli.command()
@click.argument("path", type=click.Path(writable=True), required=False)
@pass_config
def shells(config, path):
    """Plot shells."""
    import matplotlib.pyplot as plt
    from glass.ext.config import cosmo_from_config, shells_from_config
    from ._plot import use_style, plot_shells
    use_style()
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    fig = plot_shells(shells)
    if path:
        fig.savefig(path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


@cli.command()
@click.argument("path", type=click.Path(writable=True), required=False)
@pass_config
def correlations(config, path):
    """Plot correlations between shells."""
    import matplotlib.pyplot as plt
    from glass.ext.config import (cls_from_config, cosmo_from_config,
                                  shells_from_config)
    from ._plot import use_style, plot_correlations
    use_style()
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    cls = cls_from_config(config, shells, cosmo)
    accuracy = config.getfloat("plot.accuracy", 1e-2)
    fig = plot_correlations(shells, cls, accuracy=accuracy)
    if path:
        fig.savefig(path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


@cli.command()
@click.argument("path", type=click.Path(writable=True), required=False)
@pass_config
def lensing(config, path):
    """Plot lensing accuracy."""
    import matplotlib.pyplot as plt
    from glass.user import load_cls
    from glass.ext.config import (cls_from_config, cosmo_from_config,
                                  shells_from_config)
    from ._plot import use_style, plot_lensing
    use_style()
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    redshifts = config.getarray(float, "plot.lensing.redshifts")
    matter_cls = cls_from_config(config, shells, cosmo)
    lensing_cls = load_cls(config.getstr("plot.lensing.cls"))
    accuracy = config.getfloat("plot.accuracy", 1e-2)
    fig = plot_lensing(redshifts, shells, cosmo, matter_cls, lensing_cls,
                       accuracy=accuracy)
    if path:
        fig.savefig(path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
