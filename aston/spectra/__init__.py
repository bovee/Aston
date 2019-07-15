import numpy as np


class Scan(object):
    def __init__(self, x, abn, name='', source=None):
        assert len(x) == len(abn)
        self.x, self.abn = x, abn
        self.name = name
        self.source = source

    def plot(self, color=None, label=False, ax=None):
        # TODO: this is extremely ugly; needs a rewrite
        # TODO: should use source?
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if color is None:
            color = 'k'

        scn = np.vstack([self.x, self.abn])

        # determine if the spectrum is continuous
        cont_spec = scn.shape[1] > 10
        cont_spec = cont_spec and np.all(np.abs(np.diff(scn[0]) -
                                                (scn[0, 1] - scn[0, 0])) < 1e-9)  # noqa

        if cont_spec:
            # if the spacing between all the points is equal, plot as a line
            scn = scn[:, np.argsort(scn)[0]]
            ax.plot(scn[0], scn[1], '-', color=color)
        else:
            # remove 0's
            scn = scn[:, scn[1] != 0]
            try:
                # FIXME: this crashes on Windows unless the user has
                # clicked on the spectrum graph previously.
                # Matplotlib bug needs workaround
                ax.vlines(scn[0], 0, scn[1], color=color, alpha=0.5)
            except Exception:
                pass
            ax.plot(scn[0], scn[1], ',', color=color)

        cut_val = 0.01 * max(np.array(scn[1]))  # only label peaks 1% of max
        if label and cont_spec:
            l_idxs = []
            for idx in scn[1].argsort()[::-1]:
                l_idxs.append(idx)
                if idx - 1 in l_idxs or idx + 1 in l_idxs:
                    continue
                s = scn[:, idx].T
                # TODO: allow a definable max number of labels?
                # or do better collision detection between them?
                if s[1] < cut_val or len(l_idxs) > 100:
                    break
                ax.text(s[0], s[1], str(s[0]), ha='center', va='bottom',
                        rotation=90, size=10, color=color)
        elif label and not cont_spec:
            filt_scn = scn[:, 0.5 * np.roll(scn[1], 1) - scn[1] <= 0]
            for s in filt_scn[:, filt_scn[1] > cut_val].T:
                ax.text(s[0], s[1], str(s[0]), ha='center', va='bottom',
                        rotation=90, size=10, color=color)

        #    #go through the top 10% highest ions from highest to lowest
        #    #always have at least 10 labels, but no more than 50 (arbitrary)
        #    #if an ion is close to one seen previously, don't display it
        #    v2lbl = {}  # values to label
        #    plbl = []  # all values so far
        #    max_val = max(np.array(scn[1]))  # only label peaks X % of this
        #    for i in np.array(scn[1]).argsort()[::-1]:
        #        mz = scn[0][i]
        #        #don't allow a new label within 1.5 units of another
        #        if not np.any(np.abs(np.array(plbl) - mz) < 1.5) and \
        #          scn[1][i] > 0.01 * max_val:
        #            v2lbl[mz] = scn[1][i]
        #        plbl.append(mz)

        #    #add peak labels
        #    for v in v2lbl:
        #        ax.text(v, v2lbl[v], str(v), ha='center', \
        #            va='bottom', rotation=90, size=10, color=clr)
        #        #ax.text(v, v2lbl[v], str(v), ha='center', \
        #        #    va='bottom', rotation=90, size=10, color=clr, \
        #        #    bbox={'boxstyle': 'larrow,pad=0.3', 'fc': clr, \
        #        #        'ec': clr, 'lw': 1, 'alpha': '0.25'})

    @property
    def xmin(self):
        return min(self.x)

    @property
    def xmax(self):
        return max(self.x)

    @property
    def ymin(self):
        return min(self.abn)

    @property
    def ymax(self):
        return max(self.abn)

    def d13c(self):
        # FIXME: this needs to be moved to somewhere else;
        # can't get parent in here
        if self.source != 'irms':
            return None
        pass

        # dt = self.getParentOfType('file')
        # if self.info['sp-type'] == 'Isotope Standard':
        #     return dt.info['r-d13c-std']

        # # if there's no reference number, we can't do this
        # try:
        #     float(dt.info['r-d13c-std'])
        # except:
        #     return ''

        # r45std = dt.get_point('r45std', float(self.info['sp-time']))
        # r46std = dt.get_point('r46std', float(self.info['sp-time']))

        # # if no peak has been designated as a isotope std
        # if r45std == 0.0:
        #     return ''

        # d = delta13c_santrock(self.ion(44), self.ion(45), self.ion(46), \
        #          float(dt.info['r-d13c-std']), r45std, r46std)

        # return str(d)
