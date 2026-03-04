# build stage

FROM golang:1.22-alpine AS build

WORKDIR /src

COPY go.mod main.go ./

RUN go build -o /app .

# runtime stage

FROM alpine:latest

COPY --from=build /app /app

ENTRYPOINT ["/app"]