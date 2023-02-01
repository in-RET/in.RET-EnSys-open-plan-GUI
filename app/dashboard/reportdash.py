import dash
from dash import dcc, html

from django_plotly_dash import DjangoDash
import plotly.graph_objects as go
import os

from .src.inret_dash.sankey import sankey
from .src.inret_dash.plot import plot
from .src.inret_dash.es_graph import printEsGraph
from oemof import solph


app = DjangoDash('SimpleExample')

wpath = os.path.join(os.getcwd(), "dumps")
image_directory = os.path.join(os.getcwd(), "assets")

es = solph.EnergySystem()
es.restore(dpath=wpath, filename="config.dump")

#printEsGraph(es, image_directory)

busses = []
bus_figures = []

for node in es.nodes:
    if isinstance(node, solph.Bus):
        busses.append(node)

for bus in busses:
    fig = go.Figure(layout=dict(title=f"{bus} bus"))
    for t, g in solph.views.node(es.results["main"], node=bus)["sequences"].items():
        idx_asset = abs(t[0].index(bus) - 1)

        fig.add_trace(
            go.Scatter(
                x=g.index, y=g.values * pow(-1, idx_asset), name=t[0][idx_asset].label
            )
        )
    bus_figures.append(fig)

app.layout = html.Div(
    style={
        #'margin': 'auto',
        'height': '85vh',
        'width': '100%',
    },
    children=[
        html.H1(
            children='Dashboard zur Darstellung von Simulationsergebnissen',
            style={
                'textAlign': 'center'
            }
        ),

        html.Div(children='Institut für regnerative Energietechnik - In.RET, Nordhausen', style={
            'textAlign': 'center'
        }),
        
        html.Div(
            style={
                'float': 'left',
                'width': '100%',
            },
            children=[
                html.H2(
                    children='Sankey für den gesamten Zeitraum',
                    style={
                        'textAlign': 'center'
                    }
                ),
                dcc.Graph(
                    id='gesamt_sankey',
                    figure=sankey(es, es.results["main"])
                )
            ]
        ),

        #html.Div(
        #    style={
        #        'float': 'left',
        #        'width': '100%'
        #    }, 
        #    children=[
        #        html.H2(
        #            children='Energysystemgraph',
        #            style={
        #                'textAlign': 'center',
        #            }
        #        ),
        #        html.Img(
        #            style={
        #                'max-width': '100%',
        #                'margin': 'auto'
        #            },
        #            id="esgraph",
        #            src='assets/esgraph.png',
        #            width='auto'
        #        )
        #    ]
        #),

        html.Div(
            style={
                'float': 'left',
                'width': '100%',
            },
            children=[
                html.H2(
                    children='Sankey für einzelne Zeitschritte',
                    style={
                        'textAlign': 'center'
                    }
                ),
                dcc.Graph(
                    id='sankey',
                    figure=sankey(es, es.results["main"])
                ),
                dcc.Slider(
                    id='slider',
                    value=1,
                    min=0,
                    max=len(es.timeindex),
                    #marks=None,
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ]
        ),

        html.Div(
            style={
                'float': 'left',
                'width': '100%',
            },
            children=[
                dcc.Graph(id=f"{bus}-id", figure=fig,)
                for bus, fig in zip(busses, bus_figures)
            ]
        ),
    ]
)


@app.callback(
    # The value of these components of the layout will be changed by this callback
    dash.dependencies.Output(component_id="sankey", component_property="figure"),
    # Triggers the callback when the value of one of these components of the layout is changed
    dash.dependencies.Input(component_id="slider", component_property="value")
)
def update_figures(ts):
    ts = int(ts)
    # see if case changes, otherwise do not rerun this
    date_time_index = es.timeindex

    return sankey(es, es.results["main"], date_time_index[ts])
