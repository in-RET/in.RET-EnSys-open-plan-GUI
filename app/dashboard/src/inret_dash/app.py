# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import base64
from dash import Dash, dcc, html, Input, Output
import os

from .sankey import sankey
from .plot import plot
from .es_graph import printEsGraph
from oemof import solph


def run_app(name):
    app = Dash(name)

    wpath = os.path.join(os.getcwd(), "data")
    image_directory = os.path.join(os.getcwd(), "img")

    es = solph.EnergySystem()
    es.restore(dpath=wpath, filename="config.dump")

    printEsGraph(es, image_directory)

    image_filename = os.path.join(
        image_directory, "esgraph.png"
    )  # replace with your own image
    encoded_image = base64.b64encode(open(image_filename, "rb").read())

    app.layout = html.Div(
        style={"margin": "auto", "width": "100%"},
        children=[
            html.H1(children="Sankey test", style={"textAlign": "center"}),
            html.Div(
                children="Dash: A web application framework for your data.",
                style={"textAlign": "center"},
            ),
            html.Div(
                style={"float": "left", "width": "50%"},
                children=[
                    dcc.Graph(id="gesamt_sankey", figure=sankey(es, es.results["main"]))
                ],
            ),
            html.Div(
                style={"float": "left", "width": "50%"},
                children=[
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
            ),
            html.Div(
                children=[
                    html.Img(
                        style={"float": "left", "width": "50%"},
                        id="esgraph",
                        # src='data:image/png;base64,{}'.format(encoded_image)
                        src="../../img/esgraph.png",
                    )
                ]
            ),
        ],
    )

    @app.callback(
        # The value of these components of the layout will be changed by this callback
        Output(component_id="sankey", component_property="figure"),
        # Triggers the callback when the value of one of these components of the layout is changed
        Input(component_id="slider", component_property="value"),
    )
    def update_figures(ts):
        ts = int(ts)
        # see if case changes, otherwise do not rerun this
        date_time_index = es.timeindex

        return sankey(es, es.results["main"], date_time_index[ts])

    app.run_server(debug=True)
