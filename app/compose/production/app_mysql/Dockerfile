FROM python:3.9.5-alpine

ENV APP_ROOT /src
ENV CONFIG_ROOT /config
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir ${CONFIG_ROOT}
COPY requirements/mysql.txt ${CONFIG_ROOT}/requirements.txt

RUN apk update \
    && apk add --no-cache --virtual .build-deps gcc g++ musl-dev libffi-dev openssl-dev python3-dev cargo\
    && apk add libxml2-dev libxslt-dev \
    && apk add --no-cache mariadb-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r ${CONFIG_ROOT}/requirements.txt \
    && apk del .build-deps

WORKDIR ${APP_ROOT}

ADD . ${APP_ROOT}

COPY ./djangoq_setup.sh /djangoq_setup.sh
RUN chmod +x /djangoq_setup.sh

RUN adduser appUser -D -h ${APP_ROOT} -s /bin/sh \
    && chown -R appUser ${APP_ROOT}
USER appUser

CMD ["python", "manage.py", "collectstatic"]
