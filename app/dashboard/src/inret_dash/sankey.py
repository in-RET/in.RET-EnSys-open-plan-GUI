import plotly.graph_objects as go
from oemof import solph


def sankey(energy_system, results, ts=None):
    """Return a dict to a plotly sankey diagram"""
    busses = []

    labels = []
    sources = []
    targets = []
    values = []

    # draw a node for each of the network's component. The shape depends on the component's type
    for nd in energy_system.nodes:
        if isinstance(nd, solph.Bus):

            # keep the bus reference for drawing edges later
            bus = nd
            busses.append(bus)

            bus_label = bus.label

            labels.append(nd.label)

            flows = solph.views.node(results, bus_label)["sequences"]

            # draw an arrow from the component to the bus
            for component in bus.inputs:
                if component.label not in labels:
                    labels.append(component.label)

                sources.append(labels.index(component.label))
                targets.append(labels.index(bus_label))

                val = flows[((component.label, bus_label), "flow")].sum()
                if ts is not None:
                    val = flows[((component.label, bus_label), "flow")][ts]
                values.append(val)

            for component in bus.outputs:
                # draw an arrow from the bus to the component
                if component.label not in labels:
                    labels.append(component.label)

                sources.append(labels.index(bus_label))
                targets.append(labels.index(component.label))

                val = flows[((bus_label, component.label), "flow")].sum()
                if ts is not None:
                    val = flows[((bus_label, component.label), "flow")][ts]
                values.append(val)

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    hovertemplate="Node has total value %{value}<extra></extra>",
                    color="blue",
                ),
                link=dict(
                    source=sources,  # indices correspond to labels, eg A1, A2, A2, B1, ...
                    target=targets,
                    value=values,
                    hovertemplate="%{source.label} -> %{target.label}"
                    + "<br />Value: %{value}"
                    + "<br />and data <extra></extra>",
                ),
            )
        ]
    )
    if ts is not None:
        py_datetimeindexes = energy_system.timeindex.to_series()
        fig.update_layout(title_text=str(py_datetimeindexes[ts]), font_size=12)

    return fig
