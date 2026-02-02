FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod ./
COPY main.go ./

RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o todo-api .

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/todo-api .

EXPOSE 8080

CMD ["./todo-api"]
