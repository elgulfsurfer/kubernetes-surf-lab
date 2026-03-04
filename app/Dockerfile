# Stage 1 — build
FROM golang:1.22-alpine AS build

WORKDIR /src

COPY go.mod main.go ./

ARG VERSION=dev
RUN go build -ldflags "-X main.version=${VERSION}" -o /app .

# Stage 2 — runtime
FROM alpine:latest

COPY --from=build /app /app

ENTRYPOINT ["/app"]
