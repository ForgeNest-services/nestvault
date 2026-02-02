# Go (Gin) + PostgreSQL + Cloudflare R2 Example

This example demonstrates how to use **NestVault** to automatically backup a PostgreSQL database used by a Go/Gin application to Cloudflare R2.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Go/Gin    │────▶│  PostgreSQL │◀────│  NestVault  │
│   (Todo)    │     │             │     │   Backup    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Cloudflare  │
                                        │     R2      │
                                        └─────────────┘
```

## Quick Start

```bash
# 1. Copy the environment template
cp .env.tmpl .env

# 2. Edit .env with your credentials
#    - Set your Cloudflare R2 credentials
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

# Cloudflare R2 Configuration
S3_ACCESS_KEY=your_r2_access_key_id
S3_SECRET_KEY=your_r2_secret_access_key
S3_BUCKET=your_bucket_name
S3_REGION=auto
S3_ENDPOINT=https://your_account_id.r2.cloudflarestorage.com

# NestVault Configuration
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7               # Keep backups for 7 days
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8080 | Go/Gin Todo application |
| postgres | 5432 | PostgreSQL database |
| nestvault | - | Automated backup service |

## API Endpoints

- `GET /` - Health check
- `GET /todos` - List all todos
- `POST /todos` - Create a todo
- `GET /todos/:id` - Get a todo
- `PUT /todos/:id` - Update a todo
- `DELETE /todos/:id` - Delete a todo
- `GET /health` - Database health check

## Test the API

```bash
# Create a todo
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn NestVault", "completed": false}'

# List todos
curl http://localhost:8080/todos
```

## Backup Schedule

NestVault is configured to:
- Backup every 6 hours (`0 */6 * * *`)
- Retain backups for 7 days

Backups are stored in your Cloudflare R2 bucket with naming format:
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
