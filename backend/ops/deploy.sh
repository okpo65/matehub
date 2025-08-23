#!/bin/bash

# MateHub Docker Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Change to ops directory
cd "$(dirname "$0")"

# Default environment
ENVIRONMENT=${1:-development}

print_status "Deploying MateHub in $ENVIRONMENT mode..."

case $ENVIRONMENT in
    "development"|"dev")
        print_status "Starting development environment..."
        docker-compose -f docker-compose.yml up --build -d
        ;;
    "production"|"prod")
        print_status "Starting production environment..."
        
        # Check if .env file exists
        if [ ! -f .env ]; then
            print_warning ".env file not found. Creating from template..."
            cp .env.example .env
            print_warning "Please edit .env file with your production values before running again."
            exit 1
        fi
        
        docker-compose -f docker-compose.prod.yml up --build -d
        ;;
    *)
        print_error "Invalid environment. Use 'development' or 'production'"
        exit 1
        ;;
esac

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service health
print_status "Checking service health..."

# Check Redis
if docker-compose ps redis | grep -q "Up"; then
    print_status "✓ Redis is running"
else
    print_error "✗ Redis failed to start"
fi

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✓ API is running and healthy"
else
    print_warning "✗ API health check failed (may still be starting)"
fi

# Check Celery worker
if docker-compose ps celery-worker | grep -q "Up"; then
    print_status "✓ Celery worker is running"
else
    print_error "✗ Celery worker failed to start"
fi

print_status "Deployment complete!"
print_status "API available at: http://localhost:8000"
print_status "API docs available at: http://localhost:8000/docs"

if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "dev" ]; then
    print_status "Flower (Celery monitoring) available at: http://localhost:5555"
fi

print_status "To view logs: docker-compose logs -f"
print_status "To stop services: docker-compose down"
