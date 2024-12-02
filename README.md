# Welcome to the inretensys-open-plan gui repository
This is a modified version of the open_plan user interface to map the components from oemof.solph directly to the user interface. 

## Credits
Learn more about the original open_plan project on their [website](https://open-plan-tool.org/).

This code is based from previous open-source work done building a user interface to the [multi-vector-simulator](https://github.com/rl-institut/multi-vector-simulator) tool in the [Horizon2020](https://elandh2020.eu/) ELAND project. In open_plan project's scope a new design and more features are added, based on feedback collected in workshops held with stakeholders.

## Basic structure
This repository contains the code for the user interface. The simulations are performed by [inretensys-fastapi](https://github.com/in-RET/inretensys-fastapi) on a dedicated server (see the linked github repository). Once a simulation is over the results are stored locally on the simulation server and the user interface can access these files to create an result report. Also is it possible to download these files to create own, specific plots and reports.

# Getting Started

## Deploy locally

To do!

10. You can then login with `testUser` and `ASas12,.` or create your own account

## Deploy using Docker Compose
You need to be able to run docker-compose inside your terminal. If you can't you should install [Docker desktop](https://www.docker.com/products/docker-desktop/) first. 

After this step you can follow the instructions under [inretensys-common](https://github.com/in-RET/inretensys-common). This repository contains all modules which you need to run postgres, gui and api.

## Test Account
You can access a preconfigured project using the following login credentials:  `testUser:ASas12,.`
