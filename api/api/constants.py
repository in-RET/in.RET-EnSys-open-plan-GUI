import os

FTYPE_JSON = os.getenv("FTYPE_JSON", "application/json")
FTYPE_BINARY = os.getenv("FTYPE_BINARY", "application/octet-stream")

LICENSE_PATH = os.getenv("GUROBI_LICENSE_FILE_PATH", "/home/pyrokar/gurobi_docker.lic")
LOCAL_STORAGE_DIR = os.path.abspath(os.getenv("LOCAL_STORAGE_DIR", "/home/pyrokar/github/inretensys-common/data/working"))
