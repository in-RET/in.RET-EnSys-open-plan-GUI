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
    app = DjangoDash('SimpleExample')

    wpath = os.path.join(os.getcwd(), "dumps", simulation.mvs_token, "dumps")

    es = solph.EnergySystem()
    es.restore(dpath=wpath, filename="config.dump")

    #printEsGraph(es, image_directory)

    busses = []
    bus_figures = []

    results = es.results['Main']

    flows = [x for x in results.keys() if x[1] is not None]
    nodes = [x for x in results.keys() if x[1] is None]

    flows_invest = [x for x in flows if hasattr(results[x]['scalars'], 'invest') and isinstance(x[1], solph.Bus)]

    investment_elements = []  

    for flow in flows_invest:
        #investment_df[flow[0].label] = results[flow]['scalars']['invest']
        investment_elements.append(  
            html.Tr(
                children=[
                    html.Td(
                        children=flow[0].label
                    ),
                    html.Td(
                        children=str(round(results[flow]['scalars']['invest'],4))
                    )
                ],
                style={
                    'background': 'white',
                }
            ))

    #my_results = electricity_bus['scalars']

    # installed capacity of storage in GWh
    #my_results['storage_invest_GWh'] = (results[(storage, None)]['scalars']['invest']/1e6)

    # resulting renewable energy share
    #my_results['res_share'] = (1 - results[(pp_gas, bel)]['sequences'].sum()/results[(bel, demand)]['sequences'].sum())


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
        #my_results = bus['scalars']

    bus_graph =[] 
    for bus, fig in zip(busses, bus_figures):
        bus_graph.append(dcc.Graph(id=f"{bus}-id", figure=fig))
                    


    

    app.layout = html.Div(
        style = {
            'display': 'inline-block', 
            'width': '100%',
            #'margin': 'auto',
            'height': '100% !important',
            'font-family': 'Arial, Helvetica, sans-serif',
        },
        className='dashboard',
        children=[
            html.Div(
                style={
                    'box-shadow': '8px 5px 5px lightgray',
                },
                children=[
                    html.H2(
                        children='Statische Werte',
                        style={
                            'textAlign': 'center',
                        }
                    ),
                    html.H3(
                        children='Investments',
                    ),
                    html.Table(
                        style={
                            'background': 'white',
                            'width': '100%',
                            'padding' : '1em',
                        },
                        children=investment_elements
                    ),
                ]
            ),
            html.Div(
                style={
                    'float': 'left',
                    'width': '100%',
                    'box-shadow': '8px 5px 5px lightgray',
                },
                className='row',
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
                    'box-shadow': '8px 5px 5px lightgray',
                },
                className='row',
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
                    'box-shadow': '8px 5px 5px lightgray',
                },
                className='row',
                children=[
                    html.H2(
                        children='Plots für jeden Bus',
                        style={
                            'textAlign': 'center',
                        }
                    ),
                    html.Div(
                        children=bus_graph
                    )
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
