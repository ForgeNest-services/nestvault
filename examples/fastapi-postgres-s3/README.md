# FastAPI + PostgreSQL + S3 Example

This example demonstrates how to use **NestVault** to automatically backup a PostgreSQL database used by a FastAPI application to AWS S3.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  PostgreSQL │◀────│  NestVault  │
│   (Todo)    │     │             │     │   Backup    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   AWS S3    │
                                        └─────────────┘
```

## Quick Start

```bash
# 1. Copy the environment template
cp .env.tmpl .env

# 2. Edit .env with your credentials
#    - Set your S3 credentials
#    - Optionally change database credentials

# 3. Start all services
docker-compose up -d

# 4. Check NestVault logs
docker-compose logs -f nestvault
```

## Configuration

Copy `.env.tmpl` to `.env` and configure:

```bash
# Database Configuration
POSTGRES_USER=appuser
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=tododb

# S3 Configuration
S3_ACCESS_KEY=your_aws_access_key_id
S3_SECRET_KEY=your_aws_secret_access_key
S3_BUCKET=your_bucket_name
S3_REGION=us-east-1

# NestVault Configuration
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7               # Keep backups for 7 days
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI Todo application |
| postgres | 5432 | PostgreSQL database |
| nestvault | - | Automated backup service |

## API Endpoints

- `GET /` - Health check
- `GET /todos` - List all todos
- `POST /todos` - Create a todo
- `GET /todos/{id}` - Get a todo
- `PUT /todos/{id}` - Update a todo
- `DELETE /todos/{id}` - Delete a todo

## Test the API

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn NestVault", "completed": false}'

# List todos
curl http://localhost:8000/todos
```

## Backup Schedule

NestVault is configured to:
- Backup every 6 hours (`0 */6 * * *`)
- Retain backups for 7 days

Backups are stored in your S3 bucket with naming format:
```
tododb_20240115_120000.sql.gz
```

## Trigger Immediate Backup

To test backup immediately, restart the nestvault service:
```bash
docker-compose restart nestvault
```

## View Logs

```bash
# All services
docker-compose logs -f

# NestVault only
docker-compose logs -f nestvault
```

## Cleanup

```bash
docker-compose down -v  # Remove containers and volumes
```
