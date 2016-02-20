# this is used here and in the peak plotting code
def desaturate(c, k=0):
    """
    Utility function to desaturate a color c by an amount k.
    """
    from matplotlib.colors import ColorConverter
    c = ColorConverter().to_rgb(c)
    intensity = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    return [intensity * k + i * (1 - k) for i in c]


def plot_events(events, color='k', ax=None):
    from matplotlib.transforms import offset_copy
    if ax is None:
        import matplotlib.pyplot as plt
        ax = plt.gca()

    trans = ax.get_xaxis_transform()
    trans_text = offset_copy(trans, fig=ax.figure, x=3, units='points')
    for ev in events:
        t0, t1, ta = ev['t0'], ev['t1'], (ev['t0'] + ev['t1']) / 2.
        ax.vlines(t1, 0, 0.1, color=desaturate(color, 0.6), transform=trans)
        ax.vlines(t0, 0, 0.1, color=color, transform=trans)
        ax.text(ta, 0, ev['name'], ha='center', transform=trans_text)
