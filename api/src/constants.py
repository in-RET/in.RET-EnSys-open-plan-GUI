import os

FTYPE_JSON = os.getenv("FTYPE_JSON", "application/json")
FTYPE_BINARY = os.getenv("FTYPE_BINARY", "application/octet-stream")

LICENSE_PATH = os.getenv("GUROBI_LICENSE_FILE_PATH")
LOCAL_WORK_DIR = os.path.abspath(os.getenv("LOCAL_WORKDIR"))
LOCAL_DATA_DIR = os.path.abspath(os.getenv("LOCAL_DATADIR"))
