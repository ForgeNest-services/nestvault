# Go (Gin) + PostgreSQL + Cloudflare R2

Automated PostgreSQL backups to Cloudflare R2 for a Go/Gin application using NestVault.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Go/Gin    │────▶│  PostgreSQL │◀────│  NestVault  │
│    :8080    │     │    :5432    │     │   Backup    │
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
# 1. Configure credentials
cp .env.tmpl .env
# Edit .env with your Cloudflare R2 credentials

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

# Cloudflare R2
S3_ACCESS_KEY=your_r2_access_key_id
S3_SECRET_KEY=your_r2_secret_access_key
S3_BUCKET=your_bucket_name
S3_REGION=auto
S3_ENDPOINT=https://your_account_id.r2.cloudflarestorage.com

# Backup Schedule
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8080 | Go/Gin Todo application |
| postgres | 5432 | PostgreSQL database |
| nestvault | - | Automated backup service |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/todos` | List all todos |
| POST | `/todos` | Create todo |
| GET | `/todos/:id` | Get todo |
| PUT | `/todos/:id` | Update todo |
| DELETE | `/todos/:id` | Delete todo |
| GET | `/health` | Database health |

## Test

```bash
# Create a todo
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test backup", "completed": false}'

# List todos
curl http://localhost:8080/todos

# Check health
curl http://localhost:8080/health
```

## Verify Backup

1. Check NestVault logs:
   ```bash
   docker-compose logs nestvault
   ```

2. Look for successful upload message:
   ```
   [INFO] [storage.s3] Upload completed: tododb_20260202_130643.sql.gz
   ```

3. Check your bucket in Cloudflare Dashboard → R2

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

## Troubleshooting

### Access Denied on Upload
Ensure your R2 API Token has **Object Read & Write** permission:
1. Go to Cloudflare Dashboard → R2 → Manage R2 API Tokens
2. Edit or create a token with "Object Read & Write" permission
3. Apply to your specific bucket
