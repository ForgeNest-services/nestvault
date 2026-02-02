# Express.js + MongoDB + Backblaze B2

Automated MongoDB backups to Backblaze B2 for an Express.js application using NestVault.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Express.js │────▶│   MongoDB   │◀────│  NestVault  │
│    :3000    │     │   :27017    │     │   Backup    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Backblaze   │
                                        │     B2      │
                                        └─────────────┘
```

## Quick Start

```bash
# 1. Configure credentials
cp .env.tmpl .env
# Edit .env with your Backblaze B2 credentials

# 2. Start services
docker-compose up -d

# 3. Verify backup
docker-compose logs -f nestvault
```

## Configuration

Edit `.env`:

```bash
# Database
MONGO_ROOT_USER=appuser
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_DATABASE=tododb

# Backblaze B2
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET=your_bucket_name
B2_REGION=us-east-005

# Backup Schedule
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 3000 | Express.js Todo application |
| mongodb | 27017 | MongoDB database |
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
curl -X POST http://localhost:3000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test backup", "completed": false}'

# List todos
curl http://localhost:3000/todos

# Check health
curl http://localhost:3000/health
```

## Verify Backup

1. Check NestVault logs:
   ```bash
   docker-compose logs nestvault
   ```

2. Look for successful upload message:
   ```
   [INFO] [storage.backblaze] Upload completed: tododb_20260202_125444.archive.gz
   ```

3. Check your bucket in Backblaze B2 Console

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

### Authentication Failed
Ensure `?authSource=admin` is in the MongoDB URI. This is already configured in `docker-compose.yml`.

### B2 Upload Failed
Verify your B2 Application Key has write access to the bucket.
