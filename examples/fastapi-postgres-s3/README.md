# FastAPI + PostgreSQL + AWS S3

Automated PostgreSQL backups to AWS S3 for a FastAPI application using NestVault.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  PostgreSQL │◀────│  NestVault  │
│    :8000    │     │    :5432    │     │   Backup    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   AWS S3    │
                                        └─────────────┘
```

## Quick Start

```bash
# 1. Configure credentials
cp .env.tmpl .env
# Edit .env with your AWS S3 credentials

# 2. Start services
docker-compose up -d

# 3. Verify backup
docker-compose logs -f nestvault
```

## Configuration

Edit `.env`:

```bash
# Database
POSTGRES_USER=appuser
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=tododb

# AWS S3
S3_ACCESS_KEY=your_aws_access_key_id
S3_SECRET_KEY=your_aws_secret_access_key
S3_BUCKET=your_bucket_name
S3_REGION=us-east-1

# Backup Schedule
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI Todo application |
| postgres | 5432 | PostgreSQL database |
| nestvault | - | Automated backup service |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/todos` | List all todos |
| POST | `/todos` | Create todo |
| GET | `/todos/{id}` | Get todo |
| PUT | `/todos/{id}` | Update todo |
| DELETE | `/todos/{id}` | Delete todo |
| GET | `/health` | Database health |

## Test

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test backup", "completed": false}'

# List todos
curl http://localhost:8000/todos

# Check health
curl http://localhost:8000/health
```

## Verify Backup

1. Check NestVault logs:
   ```bash
   docker-compose logs nestvault
   ```

2. Look for successful upload message:
   ```
   [INFO] [storage.s3] Upload completed: tododb_20260202_124557.sql.gz
   ```

3. Check your S3 bucket in AWS Console

## Commands

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f nestvault

# Trigger immediate backup
docker-compose restart nestvault

# Stop
docker-compose down

# Stop and delete data
docker-compose down -v
```
