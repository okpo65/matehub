# Docker Deployment Guide

This directory contains Docker configuration files for deploying the MateHub FastAPI + Celery application.

## Files Overview

- `Dockerfile` - Main application container definition
- `docker-compose.yml` - Development environment setup
- `docker-compose.prod.yml` - Production environment setup
- `.dockerignore` - Files to exclude from Docker build context
- `redis.conf` - Redis configuration for production
- `nginx.conf` - Nginx reverse proxy configuration
- `.env.example` - Environment variables template
- `deploy.sh` - Automated deployment script

## Quick Start

### Development Environment

```bash
# Using the deployment script (recommended)
./deploy.sh development

# Or manually
docker-compose up --build -d
```

### Production Environment

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your production values

# Deploy
./deploy.sh production

# Or manually
docker-compose -f docker-compose.prod.yml up --build -d
```

## Services

### Development Stack
- **API**: FastAPI application (port 8000)
- **Redis**: Message broker and result backend (port 6379)
- **Celery Worker**: Background task processor
- **Flower**: Celery monitoring UI (port 5555)

### Production Stack
- **API**: FastAPI application with multiple workers
- **Redis**: Optimized Redis configuration
- **Celery Worker**: Multiple workers with task limits
- **Nginx**: Reverse proxy with rate limiting (port 80/443)

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Security
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key

# Redis
REDIS_URL=redis://redis:6379/0

# API
DEBUG=false
ENVIRONMENT=production
```

## Service URLs

### Development
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower: http://localhost:5555
- Redis: localhost:6379

### Production
- API: http://localhost (via Nginx)
- API Docs: http://localhost/docs
- Redis: Internal only

## Docker Commands

### Basic Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# Restart a service
docker-compose restart api

# Scale workers
docker-compose up -d --scale celery-worker=3
```

### Maintenance
```bash
# Rebuild containers
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v

# Clean up unused Docker resources
docker system prune -a
```

### Health Checks
```bash
# Check service status
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Celery worker status
docker-compose exec celery-worker celery -A celery_app inspect ping
```

## Production Considerations

### Security
1. **Change default secrets**: Update `SECRET_KEY` and other sensitive values
2. **Enable HTTPS**: Configure SSL certificates in Nginx
3. **Database**: Use PostgreSQL instead of SQLite for production
4. **Redis password**: Enable Redis authentication
5. **Network security**: Use Docker networks and firewall rules

### Performance
1. **Worker scaling**: Adjust Celery worker concurrency based on CPU cores
2. **Redis optimization**: Tune Redis configuration for your workload
3. **Nginx caching**: Enable caching for static content
4. **Resource limits**: Set memory and CPU limits for containers

### Monitoring
1. **Logging**: Configure centralized logging (ELK stack, etc.)
2. **Metrics**: Add Prometheus metrics collection
3. **Health checks**: Monitor service health and uptime
4. **Alerts**: Set up alerts for service failures

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change port mappings if 8000, 6379, or 5555 are in use
2. **Permission errors**: Ensure Docker has proper permissions
3. **Memory issues**: Increase Docker memory limits
4. **Network issues**: Check Docker network configuration

### Debug Commands
```bash
# Enter container shell
docker-compose exec api bash
docker-compose exec celery-worker bash

# Check container resources
docker stats

# Inspect container configuration
docker-compose config

# View container details
docker inspect matehub-api
```

### Log Analysis
```bash
# Follow all logs
docker-compose logs -f

# Filter logs by service
docker-compose logs -f api | grep ERROR

# Export logs
docker-compose logs --no-color > matehub.log
```

## Backup and Recovery

### Data Backup
```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp matehub-redis:/data/dump.rdb ./backup/

# Backup application data (if using volumes)
docker run --rm -v matehub_redis_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .
```

### Recovery
```bash
# Restore Redis data
docker cp ./backup/dump.rdb matehub-redis:/data/
docker-compose restart redis
```

## Development Workflow

1. **Code changes**: Mount source code as volumes for live reload
2. **Testing**: Run tests inside containers
3. **Debugging**: Use debugger-friendly configurations
4. **Database migrations**: Run migrations in API container

```bash
# Run tests
docker-compose exec api pytest

# Run database migrations (if using Alembic)
docker-compose exec api alembic upgrade head

# Access Python shell
docker-compose exec api python
```
