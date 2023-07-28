FROM python:3.12.0b4-bullseye

RUN apt-get update && \
    apt-get install -y libpq-dev

WORKDIR /app

RUN python -m ensurepip && \
    python -mpip install -U pip wheel

COPY requirements.txt /app/requirements.txt
RUN python -mpip install -r requirements.txt

COPY . /app

CMD python manage.py waitress