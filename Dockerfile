FROM pypy:3.8-7.3.7-bullseye

RUN apt-get update

WORKDIR /app

ENV DJANGO_SETTINGS_MODULE=scrutiny.settings.prod

RUN pypy -m ensurepip && \
    pypy -mpip install -U pip wheel

COPY requirements.txt /app/requirements.txt
RUN pypy -mpip install -r requirements.txt

COPY . /app
RUN pypy manage.py migrate --settings=scrutiny.settings.spec

CMD pypy manage.py waitress