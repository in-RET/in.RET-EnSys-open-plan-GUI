import dash
from dash import dcc, html

from django_plotly_dash import DjangoDash
import plotly.graph_objects as go
import os
import pandas as pd

from .src.inret_dash.sankey import sankey
from .src.inret_dash.plot import plot
from .src.inret_dash.es_graph import printEsGraph
from oemof import solph

from projects.models import Simulation


def createDashboard(simulation: Simulation):
    app = DjangoDash("SimpleExample")

    try:
        wpath = os.path.join(os.getcwd(), "dumps", simulation.mvs_token, "dumps")
        print(wpath)
        
        es = solph.EnergySystem()

        es.restore(dpath=wpath, filename="config.dump")
    except FileNotFoundError:
        es = None
    except Exception:
        print(Exception.with_traceback)

    if es is not None:
        # printEsGraph(es, image_directory)

        busses = []
        bus_figures = []

        results = es.results["Main"]

        flows = [x for x in results.keys() if x[1] is not None]
        nodes = [x for x in results.keys() if x[1] is None]

        flows_invest = [
            x
            for x in flows
            if hasattr(results[x]["scalars"], "invest") and isinstance(x[1], solph.Bus)
        ]

        investment_elements = []

        for flow in flows_invest:
            # investment_df[flow[0].label] = results[flow]['scalars']['invest']
            investment_elements.append(
                html.Tr(
                    children=[
                        html.Td(children=flow[0].label),
                        html.Td(
                            children=str(round(results[flow]["scalars"]["invest"], 4))
                        ),
                    ],
                    style={"background": "white"},
                )
            )

        for node in es.nodes:
            if isinstance(node, solph.Bus):
                busses.append(node)

        for bus in busses:
            fig = go.Figure(layout=dict(title=f"{bus} bus"))
            for t, g in solph.views.node(es.results["main"], node=bus)[
                "sequences"
            ].items():
                idx_asset = abs(t[0].index(bus) - 1)

                fig.add_trace(
                    go.Scatter(
                        x=g.index,
                        y=g.values * pow(-1, idx_asset),
                        name=t[0][idx_asset].label,
                    )
                )
            bus_figures.append(fig)
            # my_results = bus['scalars']

        bus_graph = []
        for bus, fig in zip(busses, bus_figures):
            bus_graph.append(dcc.Graph(id=f"{bus}-id", figure=fig))

        dashboard_childs = []

        if len(investment_elements) > 0:
            print(investment_elements)
            dashboard_childs.append(
                html.Div(
                    style={"box-shadow": "8px 5px 5px lightgray"},
                    children=[
                        html.H2(
                            children="Static values", style={"textAlign": "center"}
                        ),
                        html.H3(children="Investments"),
                        html.Table(
                            style={
                                "background": "white",
                                "width": "100%",
                                "padding": "1em",
                            },
                            children=investment_elements,
                        ),
                    ],
                )
            )

        dashboard_childs.append(
            html.Div(
                style={
                    "float": "left",
                    "width": "100%",
                    "box-shadow": "8px 5px 5px lightgray",
                },
                className="row",
                children=[
                    html.H2(
                        children="Sankey of the simulation",
                        style={"textAlign": "center"},
                    ),
                    dcc.Graph(
                        id="gesamt_sankey", figure=sankey(es, es.results["main"])
                    ),
                ],
            )
        )

        dashboard_childs.append(
            html.Div(
                style={
                    "float": "left",
                    "width": "100%",
                    "box-shadow": "8px 5px 5px lightgray",
                },
                className="row",
                children=[
                    html.H2(
                        children="Sankey of selectable single timesteps",
                        style={"textAlign": "center"},
                    ),
                    dcc.Graph(id="sankey", figure=sankey(es, es.results["main"])),
                    dcc.Slider(
                        id="slider",
                        value=1,
                        min=0,
                        max=len(es.timeindex),
                        # marks=None,
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
            )
        )

        dashboard_childs.append(
            html.Div(
                style={
                    "float": "left",
                    "width": "100%",
                    "box-shadow": "8px 5px 5px lightgray",
                },
                className="row",
                children=[
                    html.H2(
                        children="Plots for all busses", style={"textAlign": "center"}
                    ),
                    html.Div(children=bus_graph),
                ],
            )
        )

        app.layout = html.Div(
            style={
                "display": "inline-block",
                "width": "100%",
                #'margin': 'auto',
                "height": "100% !important",
                "font-family": "Arial, Helvetica, sans-serif",
            },
            className="dashboard",
            children=dashboard_childs,
        )

        @app.callback(
            # The value of these components of the layout will be changed by this callback
            dash.dependencies.Output(
                component_id="sankey", component_property="figure"
            ),
            # Triggers the callback when the value of one of these components of the layout is changed
            dash.dependencies.Input(component_id="slider", component_property="value"),
        )
        def update_figures(ts):
            ts = int(ts)
            # see if case changes, otherwise do not rerun this
            date_time_index = es.timeindex

            return sankey(es, es.results["main"], date_time_index[ts])

    else:
        try:
            # /static/working/{{ workdir }}/logs/config.log
            logfile = wpath = os.path.join(
                os.getcwd(), "dumps", simulation.mvs_token, "logs", "config.log"
            )

            file = open(logfile, "r")
            log_lines = file.readlines()
        except FileNotFoundError:
            log_lines = ["General log not found! Something went horrible wrong!"]

        log = []

        for line in log_lines:
            log.append(html.P(children=line))

        app.layout = html.Div(
            style={
                "display": "inline-block",
                "width": "100%",
                #'margin': 'auto',
                "height": "100% !important",
                "font-family": "Arial, Helvetica, sans-serif",
            },
            className="dashboard",
            children=[
                html.Div(
                    style={},
                    children=[
                        html.H1(
                            children="No Simulationdata found, please check the logs.",
                            style={"textAlign": "center"},
                        ),
                        html.H3(children="Logfile:"),
                        html.Div(children=log),
                    ],
                )
            ],
        )
