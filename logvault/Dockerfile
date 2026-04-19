FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o logvault ./cmd/logvault

FROM alpine:3.19

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /app/logvault .
COPY migrations ./migrations
COPY web ./web

EXPOSE 8080

CMD ["./logvault"]