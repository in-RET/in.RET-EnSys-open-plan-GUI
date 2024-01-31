import argparse
import os

POSTGRES = "postgres"
MYSQL = "mysql"
DB_CHOICES = (POSTGRES, MYSQL)

LOGS = {"gui": "app", "db": "db", "server": "nginx", "queues": "djangoq"}

parser = argparse.ArgumentParser(
    prog="python deploy.py",
    description="Deploy docker container to host the open-plan GUI app",
)
parser.add_argument(
    "-db",
    dest="database",
    nargs="?",
    type=str,
    default=POSTGRES,
    help=f"Database style for the open_plan app. One of ({', '.join(DB_CHOICES)}) Default: {POSTGRES}",
)
parser.add_argument(
    "--down",
    dest="docker_down",
    type=bool,
    nargs="?",
    const=True,
    default=False,
    help="Use this option if you want to take the deployed app down and clear the volumes (caution this will erase the database!)",
)
parser.add_argument(
    "--update",
    dest="docker_update",
    type=bool,
    nargs="?",
    const=True,
    default=False,
    help="Use this option if you made modification to the GUI app files and want to update the deployed app.",
)
parser.add_argument(
    "--sudo",
    dest="sudo",
    type=bool,
    nargs="?",
    const=True,
    default=False,
    help="Use this option if wou wish to run the deploy commands as sudo (posix OS only)",
)

parser.add_argument(
    "--logs",
    dest="logs",
    type=str,
    nargs="?",
    help=f"Use this option with one of ({', '.join(LOGS.keys())}) to display a log of the wished docker containers",
)


def get_docker_service_name(logs, db):
    answer = LOGS.get(logs, None)
    if db == POSTGRES and answer is not None:
        answer = f"{answer}_pg"
    return answer


if __name__ == "__main__":

    args = vars(parser.parse_args())
    db = args.get("database")
    docker_down = args.get("docker_down")
    docker_update = args.get("docker_update")
    su = args.get("sudo")
    logs = args.get("logs", None)

    if db == POSTGRES:
        app_name = "app_pg"
    elif db == MYSQL:
        app_name = "app"
    else:
        pass
    list_cmds = []

    if docker_down is True:

        if (
            input(
                "This will delete the data in your open-plan app database, are you sure you want to proceed? (Y/[n])"
            )
            != "Y"
        ):
            exit()
        list_cmds.append(f"docker-compose --file=docker-compose-{db}.yml down -v")

    if docker_update is True:
        if docker_down is False:
            list_cmds.append(f"docker-compose --file=docker-compose-{db}.yml down")
        list_cmds.append(f"docker-compose --file=docker-compose-{db}.yml up -d --build")
        list_cmds.append(
            f"docker-compose --file=docker-compose-{db}.yml exec -u root {app_name} sh update_gui.sh"
        )
    else:
        if docker_down is False:
            log_service_name = get_docker_service_name(logs, db)
            if log_service_name is not None:
                list_cmds.append(
                    f"docker-compose --file=docker-compose-{db}.yml logs {log_service_name}"
                )
            else:
                list_cmds.append(
                    f"docker-compose --file=docker-compose-{db}.yml up -d --build"
                )
                list_cmds.append(
                    f"docker-compose --file=docker-compose-{db}.yml exec -u root {app_name} sh initial_setup.sh"
                )

    for cmd in list_cmds:
        if su is True:
            cmd = f"sudo {cmd}"
        os.system(cmd)
