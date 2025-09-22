# Makefile for managing the Dockerized CV Screener application

# Use.PHONY to ensure these targets run even if files with the same name exist.
.PHONY: help build up down stop logs shell generate_cvs

# Default target when 'make' is run without arguments.
default: help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build          Build the Docker image, ignoring cache"
	@echo "  rebuild        Restart the Docker environment and rebuild the image, ignoring cache"
	@echo "  up             Start the application containers in detached mode"
	@echo "  down           Stop and remove the application containers and volumes"
	@echo "  stop           Stop the application containers without removing them"
	@echo "  logs           Follow the logs from the application container"
	@echo "  shell          Get an interactive shell inside the application container"
	@echo "  generate_cvs   Run the CV generation script inside the container"
	@echo "  create_vector_store   Run the vector store creation script inside the container"

build:
	@echo "Building Docker image (ignoring cache)..."
	docker-compose build --no-cache

rebuild:
	@echo "Restarting Docker environment and rebuilding image (ignoring cache)..."
	make down && docker-compose build --no-cache && make up

up:
	@echo "Starting Docker containers in the background..."
	docker-compose up -d && make logs

down:
	@echo "Stopping and removing Docker containers..."
	docker-compose down

stop:
	@echo "Stopping Docker containers..."
	docker-compose stop

logs:
	@echo "Following application logs... (Press Ctrl+C to exit)"
	docker-compose logs -f app

shell:
	@echo "Accessing the application container shell..."
	docker-compose exec app bash

generate_cvs:
	@echo "Generating CVs..."
	docker-compose exec app python src/generate_cvs.py

create_vector_store:
	@echo "Creating vector store..."
	docker-compose exec app python src/create_vector_store.py