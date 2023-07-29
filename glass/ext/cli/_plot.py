# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Internal module for plotting."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.transforms import (BboxBase, BboxTransformTo,
                                   blended_transform_factory)

from ._util import get_resource


def nearest_shell(redshifts, shells):
    return [np.argmin([abs(z - w.zeff) for w in shells]) for z in redshifts]


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


def figsize(w, h):
    figsize = plt.rcParams["figure.figsize"]
    return (w*figsize[0], h*figsize[1])


def plot_shells(shells):
    fig, ax = plt.subplots(1, 1, figsize=figsize(2, 1), layout="constrained")

    z = []
    for shell in shells:
        z = np.union1d(z, shell.za)
    w = np.zeros_like(z)

    for i, shell in enumerate(shells):
        if (i > 0 and shells[i-1].za[-1] == shell.za[0]
                and shells[i-1].wa[-1] == shell.wa[0]):
            w += np.interp(z, shell.za[1:], shell.wa[1:], left=0., right=0.)
        else:
            w += np.interp(z, shell.za, shell.wa, left=0., right=0.)
        ax.fill_between(shell.za, np.zeros_like(shell.wa), shell.wa,
                        ec="none", fc="C0", alpha=0.33, zorder=1)
        ax.axvline(shell.zeff, c=plt.rcParams["grid.color"],
                   ls=plt.rcParams["grid.linestyle"],
                   lw=plt.rcParams["grid.linewidth"],
                   zorder=-2)

    ax.plot(z, w, c="C1", zorder=2)

    ax.set_xlabel("redshift $z$")
    ax.set_ylabel("window function $W(z)$")

    return fig


def plot_correlations(shells, cls, *, accuracy=1e-2):

    cls = split_bins(cls)

    fig, axes = plt.subplots(4, 2, figsize=figsize(2, 4/3),
                             sharex=True, sharey=True, layout="constrained")

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
    axes[0, 0].set_yscale("symlog", linthresh=accuracy, linscale=0.45,
                          subs=None)
    axes[-1, 0].set_xlabel("angular mode number $\\ell$")
    axes[-1, 1].set_xlabel("angular mode number $\\ell$")

    symlog_no_zero(axes)

    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=0, vmax=zmax), cmap=cmap)
    cbar = fig.colorbar(sm, ax=axes, orientation="vertical",
                        label="effective redshift $\\bar{z}_i$",
                        fraction=0.04, shrink=0.5, pad=0.03)
    cbar.ax.tick_params(rotation=90)

    return fig


def plot_lensing(redshifts, shells, cosmo, matter_cls, lensing_cls, *,
                 accuracy=1e-2):

    from glass.lensing import multi_plane_matrix

    lmat = multi_plane_matrix(shells, cosmo)

    bins = nearest_shell(redshifts, shells)

    fig = plt.figure(figsize=figsize(2, len(bins)/3), layout="constrained")
    subfigs = fig.subfigures(1, 2, wspace=0.07)

    axes = subfigs[0].subplots(len(bins), 1, sharex=True, sharey=True,
                               squeeze=False)

    for i, ax in zip(bins, axes.ravel()):

        zsrc = shells[i].zeff

        ax.annotate(f"$z_s = {zsrc:.2f}$", xy=(1., 1.), xytext=(-5, -8),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="right", va="top", backgroundcolor=(1., 1., 1., 0.5))

        z = np.arange(0, np.nextafter(zsrc+0.01, zsrc), 0.01)
        w = (3*cosmo.omega_m/2*cosmo.xm(z)/cosmo.xm(zsrc)
             * cosmo.xm(z, zsrc)*(1 + z)/cosmo.ef(z))

        ax.plot(z, w, c="C1", zorder=0)
        ax.plot(z, w, c="C1", zorder=2, alpha=0.5)

        z, w = [], []
        for k in range(i+1):
            if k > 0 and shells[k-1].za[-1] == shells[k].za[0]:
                ax.plot(z, w, c="C0", zorder=1)
                z, w = [], []
            wk = lmat[i, k]*shells[k].wa/np.trapz(shells[k].wa, shells[k].za)
            if len(z) > 0:
                z_ = np.union1d(z, shells[k].za)
                z, w = z_, np.interp(z_, z, w, left=0., right=0.)
            else:
                z = shells[k].za
                w = np.zeros_like(z, dtype=float)
            w += np.interp(z, shells[k].za, wk, left=0., right=0.)
        ax.plot(z, w, c="C0", zorder=1)

        for w in shells:
            ax.axvline(w.zeff, c=plt.rcParams["grid.color"],
                       ls=plt.rcParams["grid.linestyle"],
                       lw=plt.rcParams["grid.linewidth"],
                       zorder=-2)

    axes[0, 0].margins(y=0.2)

    supxlabel(subfigs[0], "redshift $z$")
    supylabel(subfigs[0], "effective lensing kernel")

    # ---

    lensing_cls = split_bins(lensing_cls)

    n = len(shells)

    approx_cls = sum(lmat[:, i, None]*lmat[:, j, None]*getcl(matter_cls, i, j)
                     for i in range(n) for j in range(n))

    axes = subfigs[1].subplots(len(bins), 1, sharex=True, sharey=True,
                               squeeze=False)

    for i, ax, cl in zip(bins, axes.ravel(), lensing_cls):

        zsrc = shells[i].zeff

        ax.annotate(f"$z_s = {zsrc:.2f}$", xy=(1., 1.), xytext=(-5, -8),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="right", va="top", backgroundcolor=(1., 1., 1., 0.8))

        tl = cl[0][1:]
        al = approx_cls[i][1:]
        n = min(tl.size, al.size)
        l = np.arange(1, n + 1)
        sl = 1/(l + 0.5)**0.5

        ax.plot(l, (al[:n] - tl[:n])/np.fabs(tl[: n]))
        ax.fill_between(l, +sl, -sl,
                        fc=plt.rcParams["hatch.color"], ec="none", zorder=-1)

        ax.grid(True, which="major", axis="y")

    axes[0, 0].set_ylim(-90*accuracy, 90*accuracy)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set_yscale("symlog", linthresh=accuracy, linscale=0.45,
                          subs=[2, 3, 4, 5, 6, 7, 8, 9])

    supxlabel(subfigs[1], "angular mode number $\\ell$")
    supylabel(subfigs[1], "relative error $\\Delta C_\\ell^{\\kappa\\kappa}/"
              "C_\\ell^{\\kappa\\kappa}$")

    symlog_no_zero(axes)

    return fig
