FROM golang:1.16-bullseye AS go-build

RUN apt-get update && \
    apt-get install -y libbrotli-dev

WORKDIR /go/src

COPY go.mod /go/src
COPY go.sum /go/src
RUN go mod download

COPY . /go/src
RUN go build -o /go/bin/ scrutiny

FROM debian:bullseye-slim

RUN apt-get update && \
    apt-get install -y libbrotli-dev

COPY --from=go-build /go/bin/scrutiny /go/bin/scrutiny

CMD ["/go/bin/scrutiny"]