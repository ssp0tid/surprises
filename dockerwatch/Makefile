.PHONY: build run clean test lint deps

build:
	go build -o ./dockerwatch ./cmd/dockerwatch

run: build
	./dockerwatch

clean:
	rm -f ./dockerwatch

test:
	go test -v ./...

lint:
	@if command -v golangci-lint > /dev/null; then \
		golangci-lint run; \
	else \
		echo "golangci-lint not found, skipping..."; \
	fi

deps:
	go mod download
	go mod tidy