FROM pypy:3.8-7.3.7-bullseye

RUN apt-get update && \
    apt-get install -y libpq-dev

WORKDIR /app

RUN pypy -m ensurepip && \
    pypy -mpip install -U pip wheel

COPY requirements.txt /app/requirements.txt
RUN pypy -mpip install -r requirements.txt

COPY . /app

CMD pypy manage.py waitress