"""

References on Modern Color Theory:

    http://www.handprint.com/LS/CVS/color.html
"""
import os.path as op
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
from aston.tracefile.Common import TraceFile


def as_colors(dfs):
    """
    Given a dataframe containing UV-Vis data, return an array
    of RGB values corresponding to how the UV-Vis run would look.
    """
    gaussian = lambda wvs, x, w: np.exp(-0.5 * ((wvs - x) / w) ** 2)
    colors = []

    #from http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    xyz_rgb = [[3.2404542, -1.5371385, -0.4985314],
               [-0.9692660, 1.8760108, 0.0415560],
               [0.0556434, -0.2040259, 1.0572252]]
    xyz_rgb = np.array(xyz_rgb)

    for df in dfs:
        wvs = df.columns.values.astype(float)

        # set up an array modelling visual response to
        # a full spectrum
        #TODO: use http://www.ppsloan.org/publications/XYZJCGT.pdf
        vis_filt = np.zeros((3, len(wvs)))
        vis_filt[0] = 1.065 * gaussian(wvs, 595.8, 33.33) \
                    + 0.366 * gaussian(wvs, 446.8, 19.44)
        vis_filt[1] = 1.014 * gaussian(np.log(wvs), np.log(556.3), 0.075)
        vis_filt[2] = 1.839 * gaussian(np.log(wvs), np.log(449.8), 0.051)

        #from aston.peaks.PeakModels import gaussian
        #vis_filt[0] = gaussian(wvs, w=40, x=575)  # red
        #vis_filt[1] = gaussian(wvs, w=40, x=535)  # green
        #vis_filt[2] = gaussian(wvs, w=40, x=445)  # blue

        # multiply response matrix by data to get list of colors
        ab = df.values.copy()
        #trans = 10 ** (-ab)
        xyz = np.dot(ab, vis_filt.T)
        rgb = np.dot(xyz_rgb, xyz.T).T
        colors.append(rgb)

    # normalize and invert data
    #mincolor = min(np.min(c) for c in colors)
    maxcolor = max(np.max(c) for c in colors)

    for i in range(len(colors)):
        colors[i][colors[i] < 0] = 0
        #colors[i][colors[i] > 1] = 1
        #colors[i] -= mincolor
        colors[i] /= maxcolor  # - mincolor
        colors[i] = 1 - np.abs(colors[i])

    return colors


def color_strips(folder, fs, width=10, twin=None, names=None, norm_all=True):

    dfs = []
    if norm_all:
        for f in fs:
            df = TraceFile(op.join(folder, f)).data
            if twin is not None:
                df = df.select(lambda t: t >= twin[0] and t < twin[1])
            dfs.append(df)
        colors = as_colors(dfs)
    else:
        colors = []
        for f in fs:
            df = TraceFile(op.join(folder, f)).data
            if twin is not None:
                df = df.select(lambda t: t >= twin[0] and t < twin[1])
            colors.append(as_colors([df])[0])

    for i, c in enumerate(colors):
        color_mask = np.meshgrid(0, np.arange(c.shape[0], 0, -1) - 1)[1]
        ax = plt.subplot(1, len(colors), i + 1)
        ax.imshow(color_mask, cmap=ListedColormap(c), \
                  extent=(0, width, df.index[0], df.index[-1]))
        ax.xaxis.set_ticks([])
        if i != 0:
            ax.yaxis.set_ticks([])
        else:
            ax.set_ylabel('Retention Time (min)')
        if names is not None:
            ax.set_xlabel(names[i])
    plt.show()
