import os

import dash
import plotly.graph_objects as go
from dash import dcc, html
from django_plotly_dash import DjangoDash
from oemof import solph
import traceback

from projects.models import Simulation
from .src.common.automatic_cost_calc import cost_calculation_from_energysystem
from .src.inret_dash.sankey import sankey


def createDashboard(simulation: Simulation):
    app = DjangoDash("SimpleExample")

    try:
        wpath = os.path.join(os.getcwd(), "dumps", simulation.mvs_token, "dumps")
        print(wpath)

        es = solph.EnergySystem()
        es.restore(dpath=wpath, filename="config.dump")
    except FileNotFoundError as e:
        traceback.print_exc()
        es = None
    except Exception as e:
        traceback.print_exc()
        es = None

    if es is not None:
        #investment_data = cost_calculation_from_energysystem(es)

        busses = []
        bus_figures = []

        investment_elements = []
        cost_elements = []
        cost_elements_2 = []
        cost_elements_3 = []
        emissions_elements = []

        results = es.results["main"]

        flows = [x for x in results.keys() if x[1] is not None]
        nodes = [x for x in results.keys() if x[1] is None]

        for flow in [x for x in flows if hasattr(results[x]["scalars"], "invest") and isinstance(x[1], solph.Bus)]:
            print(type(flow[0]))
            print(type(flow[1]))

            if type(flow[0]) is not solph.components.GenericStorage:
                UNIT = ("MW", "kW")
            else:
                UNIT = ("MWh", "kWh")

            investment_elements.append(
                html.Tr(
                    style={"background": "white"},
                    children=[
                        html.Td(
                            style={"width": "75%"},
                            children=flow[0].label
                        ),
                        html.Td(
                            style={
                                "text-align": "right"
                            },
                            children=str("{:.4f}".format(round(results[flow]["scalars"]["invest"], 4))) + " " + UNIT[0] + " (" + str("{:.4f}".format(round(results[flow]["scalars"]["invest"] * 1000, 4))) + " " + UNIT[1] + ")"
                        )
                    ],
                )
            )

        # battery_power = solph.views.node(results, "Strombus")["scalars"][(("Batteriespeicher", "Strombus"), "invest")]
        # invest_battery = round(battery_power * 43646.22240281003, 2)
        #
        # invest_pv = round(investment_data["investment costs"]["(Photovoltaik, Strombus)"], 2)
        #
        # emission_factor = 0.380
        #
        # strom_input = round(solph.views.node(results, "Strombus")["sequences"][(("Netzanbieter", "Strombus"), "flow")].sum(), 2)
        # strom_variable_costs = round(investment_data["variable costs"]["(Netzanbieter, Strombus)"], 2)
        # strom_last = round(solph.views.node(results, "Strombus")["sequences"][(("Strombus", "Stromverbrauch"), "flow")].sum(), 2)
        # strom_export = round(solph.views.node(results, "Strombus")["sequences"][(("Strombus", "Export"), "flow")].sum(), 2)
        #
        # export_preis = 30
        # strom_preis = round(strom_variable_costs / strom_input, 0)
        # print("Strompreis:", strom_preis)
        #
        # strom_kosten = round(strom_variable_costs, 2)
        # strom_kosten_o_EE = round(strom_preis * strom_last, 2)
        # strom_einnahmen = round(export_preis * strom_export, 2)
        #
        # cost_elements.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "50%"},
        #                 children="Stromkosten p.a. (ohne Erneuerbare)"
        #             ),
        #             html.Td(
        #                 style={
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(strom_kosten_o_EE)) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_2.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "50%"},
        #                 children="Stromkosten p.a."
        #             ),
        #             html.Td(
        #                 style={"width": "25%"},
        #             ),
        #             html.Td(
        #                 style={
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(strom_kosten)) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_2.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "50%"},
        #                 children="Stromerlöse p.a."
        #             ),
        #             html.Td(
        #                 style={"width": "25%"},
        #             ),
        #             html.Td(
        #                 style={
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(strom_einnahmen)) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_3.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={
        #                     "font-weight": "bold",
        #                     "width": "75%"
        #                 },
        #                 children="Kombinierte Kosten p.a."
        #             ),
        #             html.Td(
        #                 style={
        #                     "font-weight": "bold",
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(round(strom_kosten + invest_pv + invest_battery - strom_einnahmen, 2))) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_3.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "75%"},
        #                 children="Ersparnis p.a.",
        #             ),
        #             html.Td(
        #                 style={"text-align": "right"},
        #                 children=str("{:.2f}".format(round(strom_kosten_o_EE - (strom_kosten + invest_pv + invest_battery - strom_einnahmen)), 2)) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_2.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "60%"},
        #                 children="Investitionskosten Photovoltaikanlage"
        #             ),
        #             html.Td(
        #                 style={
        #                     "width": "20%",
        #                     "text-align": "right",
        #                 },
        #                 children=str("{:.2f}".format(round(invest_pv * 25, 2))) + " €"
        #             ),
        #             html.Td(
        #                 style={
        #                     "width": "20%",
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(round(invest_pv, 2))) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # cost_elements_2.append(
        #     html.Tr(
        #         style={"background": "white"},
        #         children=[
        #             html.Td(
        #                 style={"width": "60%"},
        #                 children="Investitionskosten Batteriespeicher"
        #             ),
        #             html.Td(
        #                 style={
        #                     "width": "20%",
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(round(invest_battery * 15, 2))) + " €"
        #             ),
        #             html.Td(
        #                 style={
        #                     "width": "20%",
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.2f}".format(round(invest_battery, 2))) + " € p.a."
        #             )
        #         ]
        #     )
        # )
        #
        # input_pv = solph.views.node(results, "Strombus")["sequences"][(("Photovoltaik", "Strombus"), "flow")].sum()
        #
        # emissions_elements.append(
        #     html.Tr(
        #         children=[
        #             html.Td(
        #                 style={
        #                     "font-weight": "bold",
        #                     "width": "50%"
        #                 },
        #                 children="Emissionsersparnis"
        #             ),
        #             html.Td(
        #                 style={
        #                     "font-weight": "bold",
        #                     "text-align": "right"
        #                 },
        #                 children=str("{:.4f}".format(round(input_pv * emission_factor, 4))) + " t p.a."
        #             )
        #         ]
        #     )
        # )

        for node in es.nodes:
            if isinstance(node, solph.Bus):
                busses.append(node)

        for bus in busses:
            fig = go.Figure(layout=dict(title=f"{bus}"))
            for t, g in solph.views.node(es.results["main"], node=bus)["sequences"].items():
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

        style_dict = {
            "border-bottom": "1px solid gray",
            "background": "white",
            "width": "100%",
            "padding": "0.5em",
        }

        # if len(investment_elements) > 0:
        #     # print(investment_elements)
        #     dashboard_childs.append(
        #         html.Div(
        #             children=[
        #                 html.H2(
        #                     children="Static values", style={"textAlign": "center"}
        #                 ),
        #                 html.H3(children="Installed Power", style={"textAlign": "center"}),
        #                 html.Table(
        #                     style=style_dict,
        #                     children=investment_elements
        #                 )
        #             ]
        #         )
        #     )
        #
        # if len(cost_elements) > 0:
        #     dashboard_childs.append(
        #         html.Div(
        #             children=[
        #                 html.H3(
        #                     children="Costs", style={"textAlign": "center"}
        #                 ),
        #                 html.Table(
        #                     style=style_dict,
        #                     children=cost_elements,
        #                 ),
        #             ],
        #         )
        #     )
        #
        # if len(cost_elements_2) > 0:
        #     dashboard_childs.append(
        #         html.Div(
        #             children=[
        #                 html.Table(
        #                     style=style_dict,
        #                     children=cost_elements_2,
        #                 ),
        #             ],
        #         )
        #     )
        #
        #     if len(cost_elements_3) > 0:
        #         dashboard_childs.append(
        #             html.Div(
        #                 children=[
        #                     html.Table(
        #                         style=style_dict,
        #                         children=cost_elements_3,
        #                     ),
        #                 ],
        #             )
        #         )
        #
        #
        # if len(emissions_elements) > 0:
        #     dashboard_childs.append(
        #         html.Div(
        #
        #             children=[
        #                 html.H3(
        #                     children="Emissions", style={"textAlign": "center"}
        #                 ),
        #                 html.Table(
        #                     style=style_dict,
        #                     children=emissions_elements,
        #                 ),
        #             ],
        #         )
        #     )

        dashboard_childs.append(
            html.Div(
                style={
                    "float": "left",
                    "width": "100%",
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
        # Render Error 500

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
                html.H2(
                    children="Es ist ein Fehler passiert... Badum...",
                    style={"textAlign": "center"},
                )
            ]
        )
        pass