.PHONY: help dev prod build stop logs clean test migrate seed

help:           ## Show this help
dev:            ## Start development environment
prod:           ## Start production environment
build:          ## Build all Docker images
stop:           ## Stop all containers
logs:           ## Tail logs from all services
clean:          ## Remove all containers, volumes, and images
test:           ## Run all tests
test-backend:   ## Run backend tests
test-frontend:  ## Run frontend tests
migrate:        ## Run database migrations
seed:           ## Seed the database
lint:           ## Run linters
format:         ## Run formatters
