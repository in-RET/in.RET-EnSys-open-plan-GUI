import argparse
import logging
import os
from pathlib import Path

from InRetEnsys import ModelBuilder
from InRetEnsys.common.log import InRetEnsysLogger

parser = argparse.ArgumentParser(
    prog="main.py",
    description="InRetEnsys Backend.",
    epilog="In.RET - Institut für regenerative Energietechnik",
)

parser.add_argument("file", help="Filepath of the configuration.")
parser.add_argument(
    "-wdir",
    "--workingdirectory",
    help="Path to the workingdirectory to use.",
    default=None,
)
parser.add_argument(
    "-olp",
    "--only_lp_file",
    action="store_true",
    help="If choosen, only the lp-file is stored.",
    default=False,
    required=False,
)

args = parser.parse_args()

configfile = args.file

if args.workingdirectory is not None:
    workdir = args.workingdirectory
else:
    workdir = os.getcwd()

dumpdir = os.path.join(workdir, "dumps")
logdir = os.path.join(workdir, "logs")

tmpfilename: str = os.path.basename(configfile)

if tmpfilename.find(".json") > 0:
    dumpfile = os.path.join(dumpdir, tmpfilename.replace(".json", ".dump"))
    logfile = os.path.join(logdir, tmpfilename.replace(".json", ".log"))
elif tmpfilename.find(".bin") > 0:
    dumpfile = os.path.join(dumpdir, tmpfilename.replace(".bin", ".dump"))
    logfile = os.path.join(logdir, tmpfilename.replace(".bin", ".log"))
else:
    raise Exception("Fileformat is not valid!")

if not os.path.exists(logfile):
    os.makedirs(os.path.dirname(logfile))
    Path(logfile).touch()

InRetEnsysLogger(name="logger", filename=logfile, level=logging.DEBUG)

try:
    if args.only_lp_file:
        ModelBuilder(configfile, dumpfile, workdir, logdir, dumpdir, True)
    else:
        ModelBuilder(configfile, dumpfile, workdir, logdir, dumpdir)
except:
    raise Exception("Configuration and/or Workingdirectory incorrect!")
