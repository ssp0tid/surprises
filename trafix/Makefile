.PHONY: all build run test clean deps install docker-up docker-down

BINARY_NAME=trafix
BUILD_DIR=./bin
SRC_DIR=./src

all: deps build

deps:
	@echo "Installing dependencies..."
	cd $(SRC_DIR) && go mod download

build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	cd $(SRC_DIR) && CGO_ENABLED=1 go build -o ../$(BUILD_DIR)/$(BINARY_NAME) .

run: build
	@echo "Starting Trafix..."
	cd $(SRC_DIR)/.. && ./$(BUILD_DIR)/$(BINARY_NAME)

run-dev:
	@echo "Running in development mode..."
	cd $(SRC_DIR) && go run .

test:
	@echo "Running tests..."
	cd $(SRC_DIR) && go test -v ./...

test-coverage:
	@echo "Running tests with coverage..."
	cd $(SRC_DIR) && go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

clean:
	@echo "Cleaning up..."
	rm -rf $(BUILD_DIR)
	rm -f coverage.out coverage.html
	rm -f trafix.db

install: build
	@echo "Installing $(BINARY_NAME) to ~/go/bin..."
	cp $(BUILD_DIR)/$(BINARY_NAME) ~/go/bin/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

lint:
	@echo "Running linter..."
	cd $(SRC_DIR) && go vet ./...

fmt:
	@echo "Formatting code..."
	cd $(SRC_DIR) && go fmt ./...

tidy:
	@echo "Tidying modules..."
	cd $(SRC_DIR) && go mod tidy

.DEFAULT_GOAL := build