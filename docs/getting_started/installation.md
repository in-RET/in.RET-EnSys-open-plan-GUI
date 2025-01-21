# Installation

!!! info
    If you find some bugs don't hesitate to mail at <a href="mailto:ensys@hs-nordhausen.de">Hochschule Nordhausen</a>

!!! warning
    Not tested for Windows.

## Standalone
FastAPI: <a href="https://fastapi.tiangolo.com/" target="_blank">Documentation</a><br>
Django Framework: <a href="https://www.djangoproject.com/" target="_blank">Documentation</a>

### Example .env-File
```
# postgres settings
POSTGRES_DB=EnSys
POSTGRES_USER=ensys_pg
POSTGRES_PASSWORD=ensys_pg
POSTGRES_HOST=db
POSTGRES_PORT=5432

# pgadmin settings
PGADMIN_DEFAULT_EMAIL=admin@hs-nordhausen.de
PGADMIN_DEFAULT_PASSWORD=rootroot
PGADMIN_PORT=9005

# django settings
DJANGO_PORT=20001
DJANGO_DEBUG=False

SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=$POSTGRES_DB
SQL_USER=$POSTGRES_USER
SQL_PASSWORD=$POSTGRES_PASSWORD
SQL_HOST=$POSTGRES_HOST
SQL_PORT=$POSTGRES_PORT

EMAIL_SENDER=<mail adress>
EMAIL_HOST_IP=<mail server>
EMAIL_HOST_USER=<mail adress user>
EMAIL_HOST_PASSWORD=<mail adress password>

# api settings
LOCAL_WORKDIR=D:\Github\ensys-gui
LOCAL_DATADIR=D:\Github\ensys-gui\data\simulations
GUROBI_LICENSE_FILE_PATH=D:\Github\ensys-gui\gurobi_mvs.lic

# proxy settings
PROXY_PORT=9004
```

### Using System tools
1. Install
    - [PostgreSQL](https://www.postgresql.org/download/) 
    - [git](https://git-scm.com/downloads)
    - a Solver you want ([cbc](https://github.com/coin-or/Cbc), [gurobi](https://www.gurobi.com/))
    - [Docker](https://www.docker.com/get-started/)
2. Download the Github Repository
    - Navigate to your designated project folder
    - Download the repository for the website using
    ```
    git clone https://github.com/in-RET/ensys-gui.git
    ```
    - Download the repository for external simulation images using
    ```
    git clone https://github.com/in-RET/ensys-backend.git
    ```
3. Navigate into the backend folder (`cd ensys-backend`)
4. Run the build script
    - on Mac/Linux: `bash build.sh`
    - on Windows:
   ```
   docker build -t inretensys:0.2a7-gurobi -f .\production\gurobi\dockerfile .
   docker build -t inretensys:0.2a7-cbc -f .\production\cbc\dockerfile .
   ```
5. Navigate into the ensys-gui folder (`cd ensys-gui`)
6. Create the required .env file (example s. above)
7. Create a Virtual Environment
    ``` python
    python3 -m venv .venv
    ```
8. Start FastAPI
    ``` python
    ~: cd api    
    api: uvicorn api.api:app --host 0.0.0.0 --port 9004
    ```
9. Start Django
    ``` python
    ~: cd app
    app: python manage.py collectstatic
    app: python manage.py migrate
    app: python manage.py loaddata 'fixtures/fixture.json'
    app: python manage.py runserver 0.0.0.0:9004
    ```
10. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
11. You can then login with `testUser` and `ASas12,.` or create your own account

### Using PyCharm
1. Follow steps 1 to 4
2. Open Project in PyCharm
3. Create the required .env file (example s. above)
4. Use the Run-Configurations which are saved in the project folder
    - "Backend.run.xml" for the FastAPI-Backend
    - "Frontend.run.xml" for the Django-Frontend
    - "Offline.run.xml" Compound-run for Backend and Frontend
    - "compose.run.xml" for Docker Compose deployment
5. Run the configuration "Offline"
6. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
7. You can then login with `testUser` and `ASas12,.` or create your own account

## Docker
1. Follow steps 1 to 4
2. Install Docker
3. Navigate in the project folder
4. Create the required .env file (example s. above)
5. Type
``` bash
docker compose up
```
6. Wait until completion
7. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
8. You can then login with `testUser` and `ASas12,.` or create your own account
