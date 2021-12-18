FROM golang:1.16-bullseye AS go-build

RUN apt-get update

WORKDIR /go/src

COPY . /go/src
RUN go build -o /go/bin/ scrutiny

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

COPY --from=go-build /go/bin/scrutiny /app/bin/scrutiny

CMD pypy manage.py waitress