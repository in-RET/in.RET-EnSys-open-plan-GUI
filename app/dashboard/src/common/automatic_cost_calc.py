# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 15:50:15 2023

@author: treinhardt01, alubojanski
"""

from oemof import solph
import numpy as np
import pandas as pd

dict_costs = {"investment costs": {}, "variable costs": {}, "profits": {}}


def __cost_calculation(energysystem, results) -> pd.DataFrame:
    # % FIXME: Es liegt ein Problem damit vor, das es abhängig von der Berechnung des Systems ist.
    NODE_LIST = energysystem.node

    # print(NODE_LIST)
    tmp_node_list = []
    if type(NODE_LIST) == dict:
        for label, node in NODE_LIST.items():
            tmp_node_list.append(node)

        NODE_LIST = tmp_node_list

    for x in range(0, len(NODE_LIST)):
        for item in NODE_LIST[x].outputs.data.values():
            if (
                type(NODE_LIST[x])
                is not solph.components._generic_storage.GenericStorage
            ):
                if item.investment:
                    # Speicher wird zweimal aufgeführt, weil invest nicht im Flow() steht
                    # jetzt nur noch einmal
                    investcosts = (
                        item.investment.ep_costs[0]
                        * solph.views.node(results, item.input)["scalars"].iloc[0]
                        + item.investment.offset[0]
                        if (
                            len(item.investment.offset) > 0
                            and solph.views.node(results, item.input)["scalars"].iloc[0]
                            > 0.0
                        )
                        else 0
                    )
                    dict_costs["investment costs"].update(
                        {
                            "("
                            + str(item.input)
                            + ", "
                            + str(item.output)
                            + ")": investcosts
                        }
                    )
                    # sum_investcosts += investcosts

            if hasattr(item, "variable_costs"):
                if not all(v == 0 for v in item.variable_costs):
                    if all(val <= 0 for val in item.variable_costs):
                        erloese = np.multiply(
                            np.array(
                                solph.views.node(results, item.output)["sequences"][
                                    (item.input, item.output), "flow"
                                ][:8759]
                            ),
                            np.array(pd.Series(item.variable_costs)[:8759]),
                        )
                        dict_costs["profits"].update(
                            {
                                "("
                                + str(item.input)
                                + ", "
                                + str(item.output)
                                + ")": sum(erloese)
                            }
                        )
                        # sum_erloese += sum(erloese)

                    else:
                        line = np.multiply(
                            np.array(
                                solph.views.node(results, item.output)["sequences"][
                                    (item.input, item.output), "flow"
                                ][:8759]
                            ),
                            np.array(pd.Series(item.variable_costs)[:8759]),
                        )
                        dict_costs["variable costs"].update(
                            {
                                "("
                                + str(item.input)
                                + ", "
                                + str(item.output)
                                + ")": sum(line)
                            }
                        )
                        # sum_variablecosts += sum(line)

    return pd.DataFrame(dict_costs)


def cost_calculation_from_dump(dump_path: str, dump_file: str) -> pd.DataFrame:
    energysystem = solph.EnergySystem()
    energysystem.restore(filename=dump_file, dpath=dump_path)

    return __cost_calculation(energysystem, energysystem.results["main"])


def cost_calculation_from_energysystem(energysystem) -> pd.DataFrame:
    return __cost_calculation(energysystem, energysystem.results["main"])


def cost_calculation_from_es_and_results(energysystem, results) -> pd.DataFrame:
    return __cost_calculation(energysystem, results)
