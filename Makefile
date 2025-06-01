# ABOUTME: Makefile for common development tasks
# ABOUTME: Provides shortcuts for building, testing, and deploying

.PHONY: help install test build deploy clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make build      - Build Docker images"
	@echo "  make deploy     - Deploy infrastructure"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make dev        - Start development servers"

# Install dependencies
install: install-backend install-frontend
	@echo "✅ All dependencies installed"

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Run tests
test: test-backend test-frontend
	@echo "✅ All tests passed"

test-backend:
	@echo "Running backend tests..."
	cd backend && ./run_tests.sh

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Build Docker images
build: build-desktop build-vnc-bridge
	@echo "✅ All images built"

build-desktop:
	@echo "Building desktop container..."
	docker build -t computer-use-desktop:latest ./containers/desktop

build-vnc-bridge:
	@echo "Building VNC bridge container..."
	docker build -t computer-use-vnc-bridge:latest ./containers/vnc-bridge

# Deploy infrastructure
deploy: deploy-check deploy-terraform
	@echo "✅ Infrastructure deployed"

deploy-check:
	@echo "Checking AWS credentials..."
	aws sts get-caller-identity

deploy-terraform:
	@echo "Deploying with Terraform..."
	cd infrastructure/environments/dev && \
		terraform init && \
		terraform plan && \
		terraform apply

# Development servers
dev:
	@echo "Starting development servers..."
	@echo "Run these in separate terminals:"
	@echo "  Backend:  cd backend && uvicorn vnc_bridge.app:app --reload"
	@echo "  Frontend: cd frontend && npm run dev"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	@echo "✅ Cleaned"

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# AWS commands
ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin \
		$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

push-images: ecr-login
	docker tag computer-use-desktop:latest \
		$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/computer-use/desktop:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/computer-use/desktop:latest