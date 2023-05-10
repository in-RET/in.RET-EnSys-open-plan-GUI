FROM python:3.10

RUN echo POSTGRES
ENV APP_ROOT /src
ENV CONFIG_ROOT /config
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir ${CONFIG_ROOT}
COPY requirements/postgres.txt ${CONFIG_ROOT}/requirements.txt
COPY requirements/InRetEnsys-0.2a5-py3-none-any.whl ${CONFIG_ROOT}/InRetEnsys-0.2a5-py3-none-any.whl

RUN pip install --upgrade pip
RUN pip install -r ${CONFIG_ROOT}/requirements.txt
RUN pip install --upgrade ${CONFIG_ROOT}/InRetEnsys-0.2a5-py3-none-any.whl

WORKDIR ${APP_ROOT}

ADD . ${APP_ROOT}

COPY ./djangoq_setup.sh /djangoq_setup.sh
RUN chmod +x /djangoq_setup.sh

CMD ["python", "manage.py", "collectstatic", "--no-input"]
