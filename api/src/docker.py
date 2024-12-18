import json
import os.path

import docker
from InRetEnsys import InRetEnsysModel
from InRetEnsys.types import Solver
from fastapi.exceptions import HTTPException

from .constants import *


def io_file() -> None:
    pass


def simulate_docker(
    nameOfConfigFile, nameOfFolder, ftype, file, req_from_website=False
):
    path_internal_workdir = os.path.join("/app", "data", "simulations")
    path_api_container_workdir = os.path.join("/app", "data", "simulations", nameOfFolder)
    path_host_datadir = os.path.join(LOCAL_DATA_DIR, nameOfFolder)

    os.makedirs(path_api_container_workdir, exist_ok=True)

    api_configfile = os.path.join(path_api_container_workdir, nameOfConfigFile)

    if req_from_website and ftype == FTYPE_JSON:
        MODE = "wt"
    elif ftype == FTYPE_JSON:
        MODE = "wb"
    else:
        raise Exception("Fileformat ist not valid!")

    savefile = open(api_configfile, MODE)
    savefile.write(file)
    savefile.close()

    # reload the system to get the solvertype
    if req_from_website and ftype == FTYPE_JSON:
        MODE = "rt"
    elif ftype == FTYPE_JSON:
        MODE = "rb"
    else:
        raise Exception("Fileformat is not valid!")

    xf = open(api_configfile, MODE)
    model_dict = json.load(xf)
    model = InRetEnsysModel(**model_dict)
    xf.close()

    volumes_dict = {
        path_host_datadir: {"bind": path_internal_workdir, "mode": "rw"}
    }

    if model.solver == Solver.gurobi:
        IMAGE_TAG = "inretensys:0.2a7-gurobi"
        volumes_dict[LICENSE_PATH] = {
            "bind": os.path.join("/opt", "gurobi", "gurobi.lic"),
            "mode": "ro",
        }
    elif model.solver == Solver.cbc:
        IMAGE_TAG = "inretensys:0.2a7-cbc"
    else:
        raise Exception("Solver not implemented yet.")

    container_configfile = os.path.join(path_internal_workdir, nameOfConfigFile)

    # Verbindung zum Docker-Clienten herstellen (Server/Desktop Version)
    docker_client = docker.from_env()

    # Abfragen ob das Image existiert
    image = docker_client.images.list(IMAGE_TAG)

    # Wenn lokal kein Image existiert
    # print("Images:", image)
    if image == []:
        raise HTTPException(status_code=404, detail="Docker image not found")

    # Starten des docker-containers, im detach Mode, damit dieser das Python-Programm nicht blockiert
    container = docker_client.containers.run(
        IMAGE_TAG,
        entrypoint=["python", "main.py"],
        command="-wdir " + path_internal_workdir + " " + container_configfile,
        detach=True,
        tty=True,
        stdin_open=True,
        volumes=volumes_dict,
        name=nameOfFolder,
    )
