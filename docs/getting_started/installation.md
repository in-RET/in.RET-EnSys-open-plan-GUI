!!! info
    If you find some bugs don't hesitate to mail at <a href="mailto:ensys@hs-nordhausen.de">Hochschule Nordhausen</a>

# Standalone
FastAPI: <a href="https://fastapi.tiangolo.com/" target="_blank">Documentation</a><br>
Django Framework: <a href="https://www.djangoproject.com/" target="_blank">Document</a>

## Using System tools
1. Install Postgres as database
2. Create a Virtual Environment
``` python
python3 -m venv .venv
```
3. Start FastAPI
``` python
uvicorn api.api:app --host 0.0.0.0 --port 9004
```
4. Start Django
Navigate into the "app" folder and type:
``` python
python manage.py collectstatic
python manage.py loaddata 'fixtures/fixture.json'
python manage.py migrate
python manage.py runserver 0.0.0.0:9004
```
5. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>


## Using PyCharm
1. Open Project in PyCharm
2. Use the Run-Configurations which are saved in the project folder
   - "Backend.run.xml" for the FastAPI-Backend
   - "Frontend.run.xml" for the Django-Frontend
   - "Offline.run.xml" Compound-run for Backend and Frontend
   - "compose.run.xml" for Docker Compose deployment
3. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>

# Docker
1. Install Docker
2. Navigate in the project folder
3. Type
``` bash
docker compose up
```
4. Wait until completion
5. Open your Browser and visit <a href="http://localhost:9004" target="_blank">Local Website</a>
