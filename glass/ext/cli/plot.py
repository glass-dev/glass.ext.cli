# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Commands for making various plots."""

import os.path
import click
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.transforms import (BboxBase, BboxTransformTo,
                                   blended_transform_factory)

from .config import pass_config
from ._util import get_resource


def use_style():
    plt.style.use(get_resource("matplotlibrc"))


def getcl(cls, i, j, lmax=None):
    if j > i:
        i, j = j, i
    cl = cls[i*(i+1)//2+i-j]
    if lmax is not None:
        cl = cl[:lmax+1]
    return cl


def split_bins(a):
    s = []
    i, j = 0, 0
    while i < len(a):
        j += 1
        s.append(a[i:i+j])
        i += j
    return s


class AxesBbox(BboxBase):
    def __init__(self, axes):
        super().__init__()
        self._points = None
        self._bboxes = [ax.bbox for ax in axes]
        self.set_children(*self._bboxes)

    def get_points(self):
        if self._invalid:
            self._points = self.union(self._bboxes).get_points()
            self._invalid = 0
        return self._points


def supxlabel(fig, *args, **kwargs):
    label = fig.supxlabel(*args, **kwargs)
    trans = blended_transform_factory(BboxTransformTo(AxesBbox(fig.axes)),
                                      label.get_transform())
    label.set_transform(trans)
    return label


def supylabel(fig, *args, **kwargs):
    label = fig.supylabel(*args, **kwargs)
    trans = blended_transform_factory(label.get_transform(),
                                      BboxTransformTo(AxesBbox(fig.axes)))
    label.set_transform(trans)
    return label


def dont_draw_zero_tick(tick):
    draw = tick.draw

    def wrap(*args, **kwargs):
        if tick.get_loc() == 0.:
            tick.set_label("")
        draw(*args, **kwargs)

    return wrap


def symlog_no_zero(axes):
    for ax in np.reshape(axes, -1):
        for tick in ax.yaxis.get_major_ticks():
            tick.draw = dont_draw_zero_tick(tick)


def nearest_shell(redshifts, shells):
    return [np.argmin([abs(z - w.zeff) for w in shells]) for z in redshifts]


def plot_correlations(shells, cls):

    cls = split_bins(cls)

    fig, axes = plt.subplots(4, 2, figsize=(8, 5), sharex=True, sharey=True)

    zmax = max(w.zeff for w in shells)

    cmap = LinearSegmentedColormap.from_list("corr", ["C0", "C6", "C2"])

    for k, ax in enumerate(axes.T.flat):
        for i, w in enumerate(shells):
            if len(cls[i]) > k+1:
                r = cls[i][k+1][1:]/np.sqrt(cls[i][0][1:]*cls[i-k-1][0][1:])
                l = np.arange(1, len(r)+1)
                ax.plot(l, r, c=cmap(w.zeff/zmax), ls="-", lw=0.5)

        ax.grid(which="major", axis="y")
        ax.set_ylabel(f"$R_\\ell^{{i,i-{k+1}}}$")

    axes[0, 0].set_ylim(-0.5, 0.5)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set_yscale("symlog", linthresh=1e-2, linscale=0.45, subs=None)
    axes[-1, 0].set_xlabel("angular mode number $\\ell$")
    axes[-1, 1].set_xlabel("angular mode number $\\ell$")

    symlog_no_zero(axes)

    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=0, vmax=zmax), cmap=cmap)
    cbar = fig.colorbar(sm, ax=axes, orientation="vertical",
                        label="effective redshift $\\bar{z}_i$",
                        fraction=0.04, shrink=0.5, pad=0.03)
    cbar.ax.tick_params(rotation=90)

    return fig


def plot_lensing(redshifts, shells, cosmo, matter_cls, lensing_cls):

    from glass.lensing import multi_plane_matrix

    lensing_cls = split_bins(lensing_cls)

    lmat = multi_plane_matrix(shells, cosmo)

    bins = nearest_shell(redshifts, shells)

    fig = plt.figure(figsize=(8, 4))
    subfigs = fig.subfigures(1, 2, wspace=0.07)

    axes = subfigs[0].subplots(len(bins), 1, sharex=True, sharey=True,
                               squeeze=False).ravel()

    for i, ax in zip(bins, axes):

        zsrc = shells[i].zeff

        ax.annotate(f"$z_s = {zsrc:.2f}$", xy=(1., 1.), xytext=(-5, -8),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="right", va="top", backgroundcolor=(1., 1., 1., 0.5))

        z = np.arange(0, np.nextafter(zsrc+0.01, zsrc), 0.01)
        w = 3*cosmo.omega_m/2*cosmo.xm(z)/cosmo.xm(zsrc)*cosmo.xm(z, zsrc)*(1 + z)/cosmo.ef(z)

        ax.plot(z, w, "-", c="k", lw=0.5, zorder=1)

        for k in range(i+1):
            z = shells[k].za
            w = lmat[i, k]*shells[k].wa/np.trapz(shells[k].wa, z)
            ax.plot(z, w, c="C0", zorder=0)

        for w in shells:
            if w.zeff > zsrc:
                break
            ax.axvline(w.zeff, c=plt.rcParams["grid.color"],
                       ls=plt.rcParams["grid.linestyle"],
                       lw=plt.rcParams["grid.linewidth"],
                       zorder=-2)

    axes[0].margins(y=0.2)

    supxlabel(subfigs[0], "redshift $z$")
    supylabel(subfigs[0], "effective lensing kernel")

    # ---

    n = len(shells)

    approx_cls = sum(lmat[:, i, None]*lmat[:, j, None]*getcl(matter_cls, i, j)
                     for i in range(n) for j in range(n))

    axes = subfigs[1].subplots(len(bins), 1, sharex=True, sharey=True,
                               squeeze=False).ravel()

    for i, ax, cl in zip(bins, axes, lensing_cls):

        zsrc = shells[i].zeff

        ax.annotate(f"$z_s = {zsrc:.2f}$", xy=(1., 1.), xytext=(-5, -8),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="right", va="top", backgroundcolor=(1., 1., 1., 0.8))

        tl = cl[0][1:]
        al = approx_cls[i][1:]
        l = np.arange(1, tl.size+1)
        sl = 1/(l + 0.5)**0.5

        ax.plot(l, (al - tl)/np.fabs(tl))
        ax.fill_between(l, +sl, -sl,
                        fc=plt.rcParams["hatch.color"], ec="none", zorder=-1)

        ax.grid(True, which="major", axis="y")

    axes[0].set_ylim(-0.9, 0.9)
    axes[0].set_xscale("log")
    axes[0].set_yscale("symlog", linthresh=1e-2, linscale=0.45,
                       subs=[2, 3, 4, 5, 6, 7, 8, 9])

    supxlabel(subfigs[1], "angular mode number $\\ell$")
    supylabel(subfigs[1], "relative error $\\Delta C_\\ell^{\\kappa\\kappa}/"
                          "C_\\ell^{\\kappa\\kappa}$")

    symlog_no_zero(axes)

    return fig


@click.group()
def cli():
    """Generate various diagnostic plots."""


@cli.command()
@click.argument("path", type=click.Path(writable=True), required=False)
@pass_config
def correlations(config, path):
    """Plot correlations between shells."""
    from glass.ext.config import (cls_from_config, cosmo_from_config,
                                  shells_from_config)
    use_style()
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    cls = cls_from_config(config, shells, cosmo)
    fig = plot_correlations(shells, cls)
    if path:
        fig.savefig(path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


@cli.command()
@pass_config
@click.option("-f", "--force", is_flag=True,
              help="Force writing over existing file.")
@click.argument("method")
@click.argument("path", type=click.Path(writable=True))
def lensing_cls(config, method, path, force):
    """Compute lensing spectra for plotting."""
    from glass.shells import RadialWindow
    from glass.user import save_cls
    from glass.ext.config import (cls_from_config, cosmo_from_config,
                                  shells_from_config)
    if os.path.exists(path) and not force:
        raise click.ClickException(f"File '{path}' exists "
                                   "(use --force to overwrite)")
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    redshifts = config.getarray(float, "plot.lensing.redshifts")
    norms = []
    kerns = []
    for i in nearest_shell(redshifts, shells):
        zsrc = shells[i].zeff
        z = np.linspace(0, zsrc, 1000)
        w = 3*cosmo.omega_m/2*cosmo.xm(z)/cosmo.xm(zsrc)*cosmo.xm(z, zsrc)*(1 + z)/cosmo.ef(z)
        n = np.trapz(w, z)
        w /= n
        norms += [n]
        kerns += [RadialWindow(za=z, wa=w, zeff=zsrc)]
    config["fields.cls"] = method
    cls = cls_from_config(config, kerns, cosmo)
    iter_cls = iter(cls)
    rescaled_cls = []
    for i in range(len(norms)):
        for j in range(i, -1, -1):
            rescaled_cls.append(norms[i]*norms[j]*next(iter_cls))
    save_cls(path, rescaled_cls)


@cli.command()
@click.argument("lensing-cls", type=click.Path(exists=True, readable=True))
@click.argument("path", type=click.Path(writable=True), required=False)
@pass_config
def lensing(config, lensing_cls, path):
    """Plot lensing accuracy."""
    from glass.user import load_cls
    from glass.ext.config import (cls_from_config, cosmo_from_config,
                                  shells_from_config)
    use_style()
    cosmo = cosmo_from_config(config)
    shells = shells_from_config(config, cosmo)
    redshifts = config.getarray(float, "plot.lensing.redshifts")
    matter_cls = cls_from_config(config, shells, cosmo)
    lensing_cls = load_cls(lensing_cls)
    fig = plot_lensing(redshifts, shells, cosmo, matter_cls, lensing_cls)
    if path:
        fig.savefig(path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
