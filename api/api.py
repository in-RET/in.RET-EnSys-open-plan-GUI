from typing import List

from fastapi import FastAPI, File, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import docker
from src.constants import *
from src.docker import simulate_docker
from src.helpers import generate_random_folder

app = FastAPI()

print("STATIC_DIR", os.path.join(os.getcwd(), "api", "static"))
app.mount(os.path.join(os.getcwd(), "static"), StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="/templates")

origins = ["http://localhost", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.post("/uploadFile")
async def upload_file(
    request: Request,
    datafiles: List[UploadFile] = File(...),
):
    filelist = []

    for datafile in datafiles:
        filelist.append((await datafile.read(), datafile.content_type))

    return run_simulation(request, input=filelist)


@app.post("/uploadJson")
async def upload_file(request: Request):

    return run_simulation(
        request,
        input=[(await request.json(), FTYPE_JSON)],
        external=True,
    )


def run_simulation(request: Request, input: list = None, external=False) -> Response:
    if input is None:
        raise HTTPException(
            status_code=404, detail="No Input given!"
        )
    else:
        folderlist = []
        workdir = os.path.join(os.getcwd(), "working")
        
        for datafile, ftype in input:
            nameOfJob = generate_random_folder()

            while os.path.exists(os.path.join(workdir, nameOfJob)):
                nameOfJob = generate_random_folder()

            nameOfConfigFile = "config.json"

            simulate_docker(nameOfConfigFile, nameOfJob, ftype, datafile, external)
            folderlist.append(nameOfJob)

        if not external:
            return templates.TemplateResponse(
                "submitted.html", {"request": request, "container_list": folderlist}
            )
        else:
            return JSONResponse(
                content={"folder": folderlist},
                status_code=200,
                media_type="application/json",
            )


@app.post("/check/{token}")
async def check_container(token: str):
    # Verbindung zum Docker-Clienten herstellen (Server/Desktop Version)
#    try: 
    client = docker.from_env()
    container = client.containers.get(token)
    errors = ""
    exitcode = None

    print("State of the Container")
    print("Status:", container.attrs["State"]["Status"])
    print("Running:", container.attrs["State"]["Running"])
    print("Error:", container.attrs["State"]["Error"])
    print("ExitCode:", container.attrs["State"]["ExitCode"])

    if container.attrs["State"]["Running"] is True:
        return_status = "PENDING"
    else:
        if container.attrs["State"]["ExitCode"] == 0:
            return_status = "DONE"
        else:
            return_status = "ERROR"
            errors = container.attrs["State"]["Error"]

            log_file = os.path.join("/app/working", token, "logs", "config.log")

            if os.path.exists(log_file):
                xf = open(log_file, 'r')
                logfile_str = xf.read()
                xf.close()

                errors += logfile_str

    return JSONResponse(
        content={"status": return_status, "token": token, "error": errors, "exitcode": exitcode},
        status_code=200,
        media_type="application/json",
    )


    