import matplotlib.pyplot as plt


def plot(energy_system, results, ts=None):
    fig = plt.figure(0)

    x, y = zip(*results.items())

    plt.plot(x, y)
    plt.show()

    return fig
