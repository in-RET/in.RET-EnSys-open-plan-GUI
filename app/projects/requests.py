import json
import logging
from datetime import datetime

import httpx as requests
from dashboard.models import AssetsResults, KPICostsMatrixResults, KPIScalarResults
# from requests.exceptions import HTTPError
from epa.settings import (
    INRETENSYS_CHECK_URL,
    INRETENSYS_POST_URL,
)
from projects.constants import DONE, ERROR, PENDING

logger = logging.getLogger(__name__)


def mvs_simulation_request(data):

    try:
        # TODO: request without docker etc.
        response = requests.post(
            url=INRETENSYS_POST_URL,
            json=data,
            params={"username": "", "password": "", "docker": True},
        )

        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return None
    else:
        logger.info("The simulation was sent successfully to Inretensys API.")
        str_results = json.loads(response.content)

        return {"token": str_results["folder"][0], "status": PENDING}


def mvs_simulation_check_status(token):
    try:
        response = requests.post(INRETENSYS_CHECK_URL + token)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return None
    else:
        logger.info("Check_Satus successfully!")
        return json.loads(response.content)


def fetch_mvs_simulation_results(simulation):
    if simulation.status == PENDING:
        response = mvs_simulation_check_status(token=simulation.mvs_token)
        print("Response:", response)
        
        try:
            simulation.status = response["status"]
            simulation.errors = response["error"]
            exitcode = response["exitcode"]
            
            logger.info(f"The simulation {simulation.id} is {simulation.status}.")
        except:
            simulation.status = ERROR
            simulation.results = None

        simulation.elapsed_seconds = (datetime.now() - simulation.start_date).seconds
        simulation.end_date = (
            datetime.now() if response["status"] in [ERROR, DONE] else None
        )
        simulation.save()
    
    if simulation.status == ERROR:
        return "Error"
    elif simulation.status == PENDING:
        return "Pending"
    elif simulation.status == DONE:
        return "Done"
    else:
        return "Failure"


def get_mvs_simulation_results(simulation):
    # TODO do not repeat if the simulation is not on the server anymore, or if the results are already loaded
    if simulation.status == DONE:
        response = mvs_simulation_check_status(token=simulation.mvs_token)
        simulation.status = response["status"]
        simulation.errors = response["error"]
        
        simulation.results = (
            parse_mvs_results(simulation, response["results"]) if simulation.status == DONE else None
        )
        logger.info(f"The simulation {simulation.id} is finished")

        simulation.save()
    else:
        fetch_mvs_simulation_results(simulation)


def parse_mvs_results(simulation, response_results):
    data = json.loads(response_results)
    asset_key_list = [
        "energy_consumption",
        "energy_conversion",
        "energy_production",
        "energy_providers",
        "energy_storage",
    ]

    if not set(asset_key_list).issubset(data.keys()):
        raise KeyError("There are missing keys from the received dictionary.")

    # Write Scalar KPIs to db
    qs = KPIScalarResults.objects.filter(simulation=simulation)
    if qs.exists():
        kpi_scalar = qs.first()
        kpi_scalar.scalar_values = json.dumps(data["kpi"]["scalars"])
        kpi_scalar.save()
    else:
        KPIScalarResults.objects.create(
            scalar_values=json.dumps(data["kpi"]["scalars"]), simulation=simulation
        )
    # Write Cost Matrix KPIs to db
    qs = KPICostsMatrixResults.objects.filter(simulation=simulation)
    if qs.exists():
        kpi_costs = qs.first()
        kpi_costs.cost_values = json.dumps(data["kpi"]["cost_matrix"])
        kpi_costs.save()
    else:
        KPICostsMatrixResults.objects.create(
            cost_values=json.dumps(data["kpi"]["cost_matrix"]), simulation=simulation
        )
    # Write Assets to db
    data_subdict = {
        category: v for category, v in data.items() if category in asset_key_list
    }
    qs = AssetsResults.objects.filter(simulation=simulation)
    if qs.exists():
        asset_results = qs.first()
        asset_results.asset_list = json.dumps(data_subdict)
        asset_results.save()
    else:
        AssetsResults.objects.create(
            assets_list=json.dumps(data_subdict), simulation=simulation
        )
    return response_results

