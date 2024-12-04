# Installation

!!! info
    If you find some bugs don't hesitate to mail at <a href="mailto:ensys@hs-nordhausen.de">Hochschule Nordhausen</a>

!!! warning
    Not tested for Windows.

## Standalone
FastAPI: <a href="https://fastapi.tiangolo.com/" target="_blank">Documentation</a><br>
Django Framework: <a href="https://www.djangoproject.com/" target="_blank">Documentation</a>

### Using System tools
1. Install
    - [PostgreSQL](https://www.postgresql.org/download/) 
    - [git](https://git-scm.com/downloads)
    !!! question
        Geht das auch ohne Solver?
    - a Solver you want ([cbc](https://github.com/coin-or/Cbc), [gurobi](https://www.gurobi.com/))
    - [Docker](https://www.docker.com/get-started/)
2. Download the Github Repository
    - Navigate to your designated project folder
    - Download the repository for the website using
    ```
    git clone https://github.com/in-RET/in.RET-EnSys-open-plan-GUI.git ensys-gui
    ```
    - Download the repository for external simulation images using
    ```
    git clone https://github.com/in-RET/inretensys-backend.git ensys-backend
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
6. Create a Virtual Environment
    ``` python
    python3 -m venv .venv
    ```
7. Start FastAPI
    ``` python
    ~: cd api    
    api: uvicorn api.api:app --host 0.0.0.0 --port 9004
    ```
8. Start Django
    ``` python
    ~: cd app
    app: python manage.py collectstatic
    app: python manage.py migrate
    app: python manage.py loaddata 'fixtures/fixture.json'
    app: python manage.py runserver 0.0.0.0:9004
    ```
5. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
6. You can then login with `testUser` and `ASas12,.` or create your own account

### Using PyCharm
1. Follow steps 1 to 4
2. Open Project in PyCharm
3. Use the Run-Configurations which are saved in the project folder
    - "Backend.run.xml" for the FastAPI-Backend
    - "Frontend.run.xml" for the Django-Frontend
    - "Offline.run.xml" Compound-run for Backend and Frontend
    - "compose.run.xml" for Docker Compose deployment
4. Run the configuration "Offline"
5. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
6. You can then login with `testUser` and `ASas12,.` or create your own account

## Docker
1. Follow steps 1 to 4
2. Install Docker
3. Navigate in the project folder
4. Type
``` bash
docker compose up
```
5. Wait until completion
6. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
7. You can then login with `testUser` and `ASas12,.` or create your own account
