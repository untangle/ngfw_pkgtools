.PHONY: help build up down shell test format lint clean

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Build the Docker development environment"
	@echo "  up      - Start the Docker development environment"
	@echo "  down    - Stop the Docker development environment"
	@echo "  shell   - Open a shell in the running container"
	@echo "  test    - Run unit tests in the container"
	@echo "  format  - Format code using ruff"
	@echo "  lint    - Run linter checks using ruff"
	@echo "  clean   - Remove Docker containers and images"

# Build the Docker image
build:
	docker-compose -f docker-compose.dev.yml build

# Start the development environment
up:
	docker-compose -f docker-compose.dev.yml up -d

# Stop the development environment
down:
	docker-compose -f docker-compose.dev.yml down

# Open a shell in the running container
shell:
	docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev /bin/bash

# Run tests (excludes remote tests by default)
test:
	docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest -v --cov=lib --cov-report=term-missing -m "not remote"

# Run all tests including remote repository checks
test-remote:
	docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest -v -m remote

# Format code with ruff
format:
	docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev ruff format .

# Run linter
lint:
	docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev ruff check .

# Clean up Docker resources
clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker rmi ngfw-pkgtools:dev || true
