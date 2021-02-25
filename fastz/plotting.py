"""
Impedance plotting utilities.

.. moduleauthor:: whileman133

"""

from fastz import Z, L, C

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
from matplotlib import axes

# plot formatting options
BODE_PLOTOPTS_ZLINE = dict()
BODE_PLOTOPTS_ZLINE_ANNOTATIONS = dict()
BODE_PLOTOPTS_ZLINE_ANNOTATIONS_BBOX = dict(alpha=0.7, fc='w', ec='w')
BODE_PLOTOPTS_REFLINE = dict(ls='--', alpha=0.4, color='grey')
BODE_PLOTOPTS_REFLINE_ANNOTATIONS = dict(color='grey')
BODE_PLOTOPTS_REFLINE_ANNOTATIONS_BBOX = dict(alpha=0.7, fc='w', ec='w')


def annotation_for(z: Z) -> str:
    """
    Return a math string with the appropriate impedance formula for inductors/capacitors or
    the impedance label with subscript for other impedances.

    :param z: The impedance for which to generate the annotation.
    :return str: Annotation text.
    """

    # annotate with
    annotation_text = f"{z.prefix}_{{{z.subscript}}}"
    if type(z) is C:
        annotation_text = f"$\\frac{{1}}{{\\omega {annotation_text}}}$"
    elif type(z) is L:
        annotation_text = f"$\\omega {annotation_text}$"
    else:
        annotation_text = f"${annotation_text}$"

    return annotation_text


def bodez(targetz: Z, ff: np.ndarray, ax: axes = None, zlines='', refzlines='', **lumpedparam):
    """
    Draw the Bode magnitude plot of an impedance using matplotlib.

    :param Z targetz: The impedance object to plot.
    :param ff: Numpy array of frequencies over which to compute and plot the impedance magnitude.
    :param ax: (optional) The matplotlib axes on which to plot. A new axes is constructed if not supplied.
    :param str zlines: Whitespace-separated list of sub-impedances to plot, identified by label.
        Use the colon notation '<label>:<annotation_hp>' to specify the horizontal position of the annotation in
        plot units (frequency in Hz, scientific notation supported).
    :param str refzlines: Whitespace-separated list of sub-impedances to plot as reference lines, identified by label.
        This is commonly used to show R, L, and C impedance asymptotes.
    :param lumpedparam: Lumped parameter values to associate with the impedance before evaluating the magnitude.
    :return tuple: tuple containing the matplotlib figure and axes
    """

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = plt.gcf()

    def parse_zarg(arg: str, default_hp: float):
        """
        Parse an impedance string argument containing positioning options.
        Format expected: '<label>:<hpos>' where <label> specifies the impedance and <hpos>
        is the horizontal position (in plot units, frequency in Hz) at which to place the
        annotation for the impedance magnitude curve.

        :param str arg: The string to parse.
        :param default_hp: The default horizontal position (in plot units) of the annotation if not provided.
        :return tuple: the label and annotation horizontal positioning index for the impedance
        """

        try:
            lab, hp = arg.split(':')
        except ValueError:
            lab, hp = arg, default_hp

        # convert horizontal annotation position in plot units to index
        hp = float(hp)
        hp_index = np.argmin(np.abs(ff - hp))

        return lab, hp_index

    def plot_line(z1: Z, annotation_hpos: int, plotopts: dict, annotateopts: dict, annotateboxopts: dict):
        """Plot the specified impedance on the axes."""

        mm = abs(z1(ff, **lumpedparam))
        ax.loglog(ff, mm, **plotopts)
        annotation = ax.annotate(annotation_for(z1), (ff[annotation_hpos], mm[annotation_hpos]),
                                 ha='center', va='center', **annotateopts)
        annotation.set_bbox(dict(boxstyle='square,pad=0', **annotateboxopts))

    # parse and collect impedance line specifications
    zlinespec = {label: hp for label, hp in [parse_zarg(arg, default_hp=ff[-1]) for arg in zlines.split()]}
    reflinespec = {label: hp for label, hp in [parse_zarg(arg, default_hp=ff[0]) for arg in refzlines.split()]}

    # fetch the horizontal position of the top-level impedance annotation if given in the specifications
    if targetz.label in zlinespec:
        hpos_idx = zlinespec.pop(targetz.label)
    else:
        hpos_idx = -1

    # plot top-level impedance curve
    plot_line(targetz, hpos_idx, BODE_PLOTOPTS_ZLINE, BODE_PLOTOPTS_ZLINE_ANNOTATIONS,
              BODE_PLOTOPTS_ZLINE_ANNOTATIONS_BBOX)

    # plot additional impedance curves
    for label, hpos_idx in zlinespec.items():
        plot_line(targetz.subz(label), hpos_idx, BODE_PLOTOPTS_ZLINE, BODE_PLOTOPTS_ZLINE_ANNOTATIONS,
                  BODE_PLOTOPTS_ZLINE_ANNOTATIONS_BBOX)

    # plot reference curves
    for label, hpos_idx in reflinespec.items():
        plot_line(targetz.subz(label), hpos_idx, BODE_PLOTOPTS_REFLINE, BODE_PLOTOPTS_REFLINE_ANNOTATIONS,
                  BODE_PLOTOPTS_REFLINE_ANNOTATIONS_BBOX)

    # set axis labels
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Impedance Magnitude ($\\Omega$)')

    # use engineering notation for frequency axis
    ax.xaxis.set_major_formatter(EngFormatter())

    return fig, ax
