FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


ENV APP_ROOT /app
ENV CONFIG_ROOT /config

RUN mkdir ${CONFIG_ROOT}
COPY requirements/ ${CONFIG_ROOT}/

RUN pip install --upgrade pip
RUN pip install -r ${CONFIG_ROOT}/requirements.txt
RUN pip install --upgrade ${CONFIG_ROOT}/InRetEnsys-0.2a7-py3-none-any.whl

WORKDIR ${APP_ROOT}

COPY /app/ ${APP_ROOT}

CMD ["python", "manage.py", "collectstatic", "--no-input"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]