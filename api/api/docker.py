import json

from InRetEnsys import InRetEnsysModel
from InRetEnsys.types import Solver
from fastapi.exceptions import HTTPException

import docker
from .constants import *


def simulate_docker(nameOfConfigFile, nameOfFolder, ftype, file, req_from_website=False):
    pathOfInternalWorkDir = "/app/working"
    pathOfDockerWorkDir = os.path.join(pathOfInternalWorkDir, nameOfFolder)
    pathOfExternalWorkDir = os.path.join(LOCAL_STORAGE_DIR, nameOfFolder)
    os.makedirs(pathOfDockerWorkDir)

    licensepath = LICENSE_PATH
    pathOfConfigfile = os.path.join(pathOfDockerWorkDir, nameOfConfigFile)

    if req_from_website and ftype == FTYPE_JSON:
        MODE = "wt"
    elif ftype == FTYPE_JSON:
        MODE = "wb"
    else:
        raise Exception("Fileformat ist not valid!")
    
    savefile = open(pathOfConfigfile, MODE)
    savefile.write(file)
    savefile.close()

    # reload the system to get the solvertype
    if req_from_website and ftype == FTYPE_JSON:
        MODE = "rt"   
    elif ftype == FTYPE_JSON:
        MODE = "rb"
    else:
        raise Exception("Fileformat is not valid!")

    xf = open(pathOfConfigfile, MODE)
    model_dict = json.load(xf)
    model = InRetEnsysModel(**model_dict)
    xf.close()
    
    volumes_dict = {pathOfExternalWorkDir: {"bind": pathOfInternalWorkDir, "mode": "rw"}}

    if model.solver == Solver.gurobi:
        IMAGE_TAG = "inretensys:0.2a7-gurobi"
        volumes_dict[licensepath] = {"bind": "/opt/gurobi/gurobi.lic", "mode": "ro"}
    elif model.solver == Solver.cbc:
        IMAGE_TAG = "inretensys:0.2a7-cbc"
    else:
        raise Exception("Solver not implemented yet.")

    internalConfigFile = os.path.join(pathOfInternalWorkDir, nameOfConfigFile)

    # Verbindung zum Docker-Clienten herstellen (Server/Desktop Version)
    docker_client = docker.from_env()

    # Abfragen ob das Image existiert
    image = docker_client.images.list(IMAGE_TAG)

    # Wenn lokal kein Image existiert
    if image == []:
        raise HTTPException(status_code=404, detail="Docker image not found")

    print("Verzeichnisübersicht")
    print("Ext.:", pathOfExternalWorkDir)
    print("Int.:", pathOfInternalWorkDir)
    print("Docker:", pathOfDockerWorkDir)
    print("Config:", pathOfConfigfile)
    print("Int.Config:", internalConfigFile)
    print("Volumes_dict", volumes_dict)

    # Starten des docker-containers, im detach Mode, damit dieser das Python-Programm nicht blockiert
    container = docker_client.containers.run(
        IMAGE_TAG,
        entrypoint=["python", "main.py"],
        command="-wdir " + pathOfInternalWorkDir + " " + internalConfigFile,
        detach=True,
        volumes=volumes_dict,
        name=nameOfFolder,
    )
