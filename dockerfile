FROM python:3.12

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_ROOT /app
ENV CONFIG_ROOT /config

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install git libpq-dev gcc libc-dev libhdf5-dev
RUN apt-get -y install python3-h5py

RUN apt autoclean

RUN mkdir ${CONFIG_ROOT}
COPY requirements/ ${CONFIG_ROOT}/

RUN pip install --upgrade pip
RUN pip install -r ${CONFIG_ROOT}/requirements.txt
RUN pip install --upgrade ${CONFIG_ROOT}/InRetEnsys-0.2a7-py3-none-any.whl

WORKDIR ${APP_ROOT}

COPY /app/ ${APP_ROOT}

RUN python manage.py migrate
RUN python manage.py collectstatic --no-input
RUN python manage.py loaddata 'fixtures/fixture.json'
