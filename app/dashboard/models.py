import json

from django.utils.translation import ugettext_lazy as _
from django.db import models
from projects.models import Simulation

KPI_COSTS_TOOLTIPS = {
    "Replacement_costs_during_project_lifetime": "Costs for replacement of assets which occur over the project lifetime.",
    "annuity_om": "Annuity of the operation, maintenance and dispatch costs of the energy system, ie. Ballpoint number of the annual expenses for system operation.",
    "annuity_total": "Annuity of the net present costs (NPC) of the energy system.", 
    "costs_cost_om": "Costs for fix annual operation and maintenance costs over the whole project lifetime, that do not depend on the assets dispatch but solely on installed capacity.",
    "costs_dispatch": "Dispatch costs over the whole project lifetime including all expenditures that depend on the dispatch of assets, ie. fuel costs, electricity consumption from the external grid, costs for operation and maintainance that depend on the thoughput of an asset.",
    "costs_investment_over_lifetime": "Investment costs over the whole project lifetime, including all replacement costs.",
    "costs_om_total": "Costs for annual operation and maintenance costs as well as dispatch of all assets of the energy system, for the whole project duration.",
    "costs_total": "Net present costs of the system for the whole project duration, includes all operation, maintainance and dispatch costs as well as the investment costs (including replacements).",
    "costs_upfront_in_year_zero": "The costs which will have to be paid upfront when project begin, ie. In year 0.",
    "levelized_cost_of_energy_of_asset": "Cost per kWh thoughput though an asset, based on the assets costs during the project lifetime as well as the total thoughput though the asset in the project lifetime. For generation assets, equivalent to the levelized cost of generation."
}

KPI_COSTS_UNITS = {
    "Replacement_costs_during_project_lifetime": "currency",
    "annuity_om": "currency/annum",
    "annuity_total": "currency/annum",
    "costs_cost_om": "currency",
    "costs_dispatch": "currency",
    "costs_investment_over_lifetime": "currency",
    "costs_om_total": "currency/annum",
    "costs_total": "currency",
    "costs_upfront_in_year_zero": "currency",
    "levelized_cost_of_energy_of_asset": "currency/kWh", 
}

KPI_SCALAR_UNITS = {
    "Attributed costsElectricity": "currency",
    "Degree of autonomy": "fraction",
    "Levelized costs of electricity equivalent": "currency/kWh",
    "Levelized costs of electricity equivalentElectricity": "currency/kWh",
    "Onsite energy fraction": "fraction",
    "Onsite energy matching": "fraction",
    "Renewable factor": "fraction",
    "Renewable share of local generation": "fraction",
    "Replacement_costs_during_project_lifetime": "currency",
    "Specific emissions per electricity equivalent": "kg GHGeq/kWh",
    "Total emissions": "GHGeq/annum",
    "Total internal generation": "kWh/annum",
    "Total internal non-renewable generation": "kWh/annum",
    "Total internal renewable generation": "kWh/annum",
    "Total non-renewable energy use": "kWh/annum",
    "Total renewable energy use": "kWh/annum",
    "Total_demandElectricity": "kWh/annum",
    "Total_demandElectricity_electricity_equivalent": "kWh/annum",
    "Total_demand_electricity_equivalent": "kWh/annum",
    "Total_excessElectricity": "kWh/annum",
    "Total_excessElectricity_electricity_equivalent": "kWh/annum",
    "Total_excess_electricity_equivalent": "kWh/annum",
    "Total_feedinElectricity": "kWh/annum",
    "Total_feedinElectricity_electricity_equivalent": "kWh/annum",
    "Total_feedin_electricity_equivalent": "kWh/annum",
    "annuity_om": "currency/annum",
    "annuity_total": "currency/annum",
    "costs_cost_om": "currency",
    "costs_dispatch": "currency",
    "costs_investment_over_lifetime": "currency",
    "costs_om_total": "currency",
    "costs_total": "currency",
    "costs_upfront_in_year_zero": "currency"
}

KPI_SCALAR_TOOLTIPS = {
    "Attributed costsElectricity": "Costs attributed to supplying the electricity sectors demand, based on Net Present Costs of the energy system and the share of electricity compared to the overall system demand.",
    "Degree of autonomy": "A degree of autonomy close to zero shows high dependence on the DSO, while a degree of autonomy of 1 represents an autonomous or net-energy system and a degree of autonomy higher 1 a surplus-energy system",
    "Levelized costs of electricity equivalent": "Levelized cost of energy of the sector-coupled energy system, calculated from the systems annuity and the total system demand in electricity equivalent.",
    "Levelized costs of electricity equivalentElectricity": "Levelized cost of electricity, calculated from the levelized cost of energy and the share that the electricity demand has of the total energy demand of the system.",
    "Onsite energy fraction": "Onsite energy fraction is also referred to as self-consumption. It describes the fraction of all locally generated energy that is consumed by the system itself.",
    "Onsite energy matching": "The onsite energy matching is also referred to as self-sufficienct. It describes the fraction of the total demand that can be covered by the locally generated energy. Notice that the feed into the grid should only be positive. https://mvs-eland.readthedocs.io/en/latest/MVS_Outputs.html#onsite-energy-matching-oem",
    "Renewable factor": "Describes the share of the energy influx to the local energy system that is provided from renewable sources. This includes both local generation as well as consumption from energy providers.",
    "Renewable share of local generation": "The renewable share of local generation describes how much of the energy generated locally is produced from renewable sources. It does not take into account the consumption from energy providers.",
    "Replacement_costs_during_project_lifetime": "Costs for replacement of assets which occur over the project lifetime.",
    "Specific emissions per electricity equivalent": "Specific GHG emissions per supplied electricity equivalent",
    "Total emissions": "Total greenhouse gas emissions in kg.",
    "Total internal generation": "Aggregated amount of energy generated within the energy system",
    "Total internal non-renewable generation": "Aggregated amount of non-renewable energy generated within the energy system",
    "Total internal renewable generation": "Aggregated amount of renewable energy generated within the energy system",
    "Total non-renewable energy use": "Aggregated amount of non-renewable energy used within the energy system (ie. Including local generation and external supply).",
    "Total renewable energy use": "Aggregated amount of renewable energy used within the energy system (ie. Including local generation and external supply).",
    "Total_demandElectricity": "Demand of electricity in local energy system.",
    "Total_demandElectricity_electricity_equivalent": "Demand of electricity in local energy system, in electricity equivalent. This is equivalent to Electricity feed-in.",
    "Total_demand_electricity_equivalent": "System wide demand from all energy vectors, in electricity equivalent.",
    "Total_excessElectricity": "Excess of electricity / unused electricity in local energy system.",
    "Total_excessElectricity_electricity_equivalent": "Excess of electricity / unused electricity in local energy system, in electricity equivalent. This is equivalent to Excess electricity.",
    "Total_excess_electricity_equivalent": "System-wide excess of energy / unused energy, in electricity equivalent.",
    "Total_feedinElectricity": "Feed-in of electricity into external grid.",
    "Total_feedinElectricity_electricity_equivalent": "Feed-in of electricity into external grid, in electricity equivalent. This is equivalent to Electricity feed-in.",
    "Total_feedin_electricity_equivalent": "System wide feed-in into external grids from all energy vectors, in electricity equivalent.",
    "annuity_om": "Annuity of the operation, maintenance and dispatch costs of the energy system, ie. Ballpoint number of the annual expenses for system operation.",
    "annuity_total": "Annuity of the net present costs (NPC) of the energy system.",
    "costs_cost_om": "Costs for fix annual operation and maintenance costs over the whole project lifetime, that do not depend on the assets dispatch but solely on installed capacity.",
    "costs_dispatch": "Dispatch costs over the whole project lifetime including all expenditures that depend on the dispatch of assets, ie. fuel costs, electricity consumption from the external grid, costs for operation and maintainance that depend on the thoughput of an asset",
    "costs_investment_over_lifetime": "Investment costs over the whole project lifetime, including all replacement costs.",
    "costs_om_total": "Costs for annual operation and maintenance costs as well as dispatch of all assets of the energy system, for the whole project duration.",
    "costs_total": "Net present costs of the system for the whole project duration, includes all operation, maintainance and dispatch costs as well as the investment costs (including replacements).",
    "costs_upfront_in_year_zero": "The costs which will have to be paid upfront when project begin, ie. In year 0."
}

# TODO have this in a csv structure to also create the doc and tool tips
GRAPH_TIMESERIES = "timeseries"
GRAPH_TIMESERIES_STACKED = "timeseries_stacked"
GRAPH_CAPACITIES = "capacities"
GRAPH_BAR = "bar"
GRAPH_PIE = "pie"
GRAPH_LOAD_DURATION = "load_duration"
GRAPH_SANKEY = "sankey"

REPORT_TYPES = (
    (GRAPH_TIMESERIES, _("Timeseries graph")),
    (GRAPH_TIMESERIES_STACKED, _("Stacked timeseries graph")),
    (GRAPH_CAPACITIES, _("Installed and optimized capacities")),
    (GRAPH_BAR, _("Bar chart")),
    (GRAPH_PIE, _("Pie chart")),
    (GRAPH_LOAD_DURATION, _("Load duration curve")),
    (GRAPH_SANKEY, _("Sankey diagram")),
)

class KPIScalarResults(models.Model):
    scalar_values = models.TextField()  # to store the scalars dict
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)


class KPICostsMatrixResults(models.Model):
    cost_values = models.TextField()  # to store the scalars dict
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)


class AssetsResults(models.Model):
    assets_list = models.TextField()  # to store the assets list
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
    __asset_names = None
    __available_timseries = None
    __asset_categories = None

    @property
    def assets_dict(self):
        try:
            answer = json.loads(self.assets_list)
        except json.decoder.JSONDecodeError:
            answer = {}
        return answer

    @property
    def asset_names(self):
        if self.__asset_names is None:
            self.__asset_names = []
            asset_dict = self.assets_dict
            for category in asset_dict:
                for asset in asset_dict[category]:
                    self.__asset_names.append(asset["label"])
        return self.__asset_names

    @property
    def available_timeseries(self):
        """Returns a dict which keys are asset labels and values are asset results only for timeseries asset

        An asset is deemed a timeseries when its results contain the key "flow"
        """
        if self.__available_timseries is None:
            self.__available_timseries = {}
            asset_dict = self.assets_dict
            for category in asset_dict:
                for asset in asset_dict[category]:
                    if "flow" in asset and "_consumption_period" not in asset["label"]:
                        asset["category"] = category
                        self.__available_timseries[asset["label"]] = asset
        return self.__available_timseries

    @property
    def asset_categories(self):
        if self.__asset_categories is None:
            self.__asset_categories = tuple(self.assets_dict.keys())
        return self.__asset_categories

    def single_asset_results(self, asset_name, asset_category=None):
        """Provided the name of an asset, return the results linked to this asset"""
        asset_dict = self.assets_dict
        answer = None
        if asset_category is not None:
            categories = [asset_category]
        else:
            categories = self.__asset_categories

        for category in categories:
            for asset in asset_dict[category]:
                if asset_name == asset["label"]:
                    if answer is None:
                        answer = asset
                        answer["category"] = category
                        break
                    else:
                        raise ValueError(
                            f"Asset named {asset_name} appears twice in simulations results, this should not be possible"
                        )
        return answer

    def single_asset_timeseries(self, asset_name, asset_category=None):
        """Provided the user name of the asset, return the timeseries linked to this asset"""
        if self.__available_timeseries is None:
            asset_results = self.single_asset_results(asset_name, asset_category)

        else:
            asset_results = self.__available_timeseries.get(asset_name)

        if "flow" in asset_results:
            answer = {
                "value": asset_results["flow"]["value"],
                "unit": asset_results["flow"]["unit"],
                "label": asset_name,
            }
        else:
            return None
# # TODO change the form from this model to adapt the choices depending on single scenario/compare scenario or sensitivity
class ReportItem(models.Model):
    title = models.CharField(max_length=120, default="", blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    simulations = models.ManyToManyField(Simulation)
    parameters = models.TextField(
        default="", blank=True
    )  # to store the parameter lists
    initial_simulations = None

    def __init__(self, *args, **kwargs):
        if "simulations" in kwargs:
            self.initial_simulations = kwargs.pop("simulations")
            self.initial_simulations = self.__parse_simulation_list(
                self.initial_simulations
            )
        super().__init__(*args, **kwargs)

    #
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.initial_simulations is not None:
            self.simulations.add(*self.initial_simulations)

    def update_simulations(self, list_simulation):
        list_simulation = self.__parse_simulation_list(list_simulation)
        if list_simulation:
            self.simulations.clear()
            self.simulations.add(*list_simulation)

    def __parse_simulation_list(self, simulation_list):
        if not isinstance(simulation_list, list):
            simulation_list = [simulation_list]

        if len(simulation_list) > 0:
            if isinstance(simulation_list[0], int):
                simulation_list = [
                    s for s in Simulation.objects.filter(id__in=simulation_list)
                ]
        return simulation_list

    @property
    def parameters_dict(self):
        try:
            answer = json.loads(self.parameters)
        except json.decoder.JSONDecodeError:
            answer = {}
        return answer
