.PHONY: build test clean install lint

BINARY_NAME=secret-vault
VERSION=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
LDFLAGS=-ldflags "-s -w -X main.version=$(VERSION) -X main.buildTime=$(BUILD_TIME)"

build:
	go build $(LDFLAGS) -o $(BINARY_NAME) .

test:
	go test -v -race -coverprofile=coverage.out ./...

clean:
	rm -f $(BINARY_NAME) coverage.out

install: build
	mkdir -p ~/.local/bin
	cp $(BINARY_NAME) ~/.local/bin/

lint:
	golangci-lint run ./...