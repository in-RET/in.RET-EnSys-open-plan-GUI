import os
from oemof_visio import ESGraphRenderer


def printEsGraph(es, wdir):
    ESGraphRenderer(
        energy_system=es, filepath=os.path.join(wdir, "esgraph.png"), img_format="png"
    ).render()
