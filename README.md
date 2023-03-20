# Welcome to the inretensys-open-plan gui repository
This is a modified version of the open_plan user interface to map the components from oemof.solph directly to the user interface. 

## Credits
Learn more about the original open_plan project on their [website](https://open-plan-tool.org/).

This code is based from previous open-source work done building a user interface to the [multi-vector-simulator](https://github.com/rl-institut/multi-vector-simulator) tool in the [Horizon2020](https://elandh2020.eu/) ELAND project. In open_plan project's scope a new design and more features are added, based on feedback collected in workshops held with stakeholders.

## Basic structure
This repository contains the code for the user interface. The simulations are performed by [inretensys-fastapi](https://github.com/in-RET/inretensys-fastapi) on a dedicated server (see the linked github repository). Once a simulation is over the results are stored locally on the simulation server and the user interface can access these files to create an result report. Also is it possible to download these files to create own, specific plots and reports.

# Getting Started

## Deploy locally using and using our inretensys-fastapi

Prior to be able to develop locally, you might need to install postgres, simply google `install postgres` followed by your os name (`linux/mac/windows`)

1. Create a virtual environment
2. Activate your virtual environment
3. Install the dependencies with `pip install -r app/requirements/postgres.txt`
4. Install extra local development dependencies with `pip install -r app/dev_requirements.txt`
5. Move to the `app` folder with `cd app`
6. Create environment variables (only replace content surrounded by `<>`)
```
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=<your db name>
SQL_USER=<your user name>
SQL_PASSWORD=<your password>
SQL_HOST=localhost
SQL_PORT=5432
DEBUG=(True|False)
```
8. Execute the `local_setup.sh` file (`. local_setup.sh` on linux/mac `bash local_setup.sh` on windows) you might have to make it executable first. Answer yes to the question
9. Start the local server with `python manage.py runserver`
10. You can then login with `testUser` and `ASas12,.` or create your own account

## Deploy using Docker Compose
You need to be able to run docker-compose inside your terminal. If you can't you should install [Docker desktop](https://www.docker.com/products/docker-desktop/) first. 

After this step you can follow the instructions under [inretensys-common](https://github.com/in-RET/inretensys-common). This repository contains all modules which you need to run postgres, gui and api.

## Test Account
You can access a preconfigured project using the following login credentials:  `testUser:ASas12,.`