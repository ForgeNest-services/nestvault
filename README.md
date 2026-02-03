# NestVault

[![GitHub Release](https://img.shields.io/github/v/release/ForgeNest-services/nestvault)](https://github.com/ForgeNest-services/nestvault/releases)
[![Docker Image](https://img.shields.io/docker/v/forgenestservices/nestvault?label=Docker)](https://hub.docker.com/r/forgenestservices/nestvault)

Container-native backup utility for PostgreSQL and MongoDB with S3-compatible storage backends.

## Why NestVault?

- **Zero Configuration in Your App** - NestVault runs as a sidecar container, no SDK or code changes required
- **Cloud Native** - Designed for Docker and Kubernetes deployments
- **Multiple Storage Backends** - AWS S3, Cloudflare R2, Backblaze B2
- **Automatic Retention** - Set it and forget it, old backups are automatically cleaned up
- **Cron Scheduling** - Flexible scheduling with standard cron expressions

## Features

- **Database Support**: PostgreSQL and MongoDB
- **Storage Backends**: Amazon S3, Cloudflare R2, Backblaze B2
- **Scheduled Backups**: Cron-based scheduling (UTC)
- **Retention Policies**: Automatic cleanup of old backups
- **Compressed Backups**: All backups are gzip compressed
- **Structured Logging**: JSON-formatted logs with loguru

## Quick Start

Pull the image:

```bash
# From GitHub Container Registry (recommended)
docker pull ghcr.io/forgenest-services/nestvault:latest

# Or from Docker Hub
docker pull forgenestservices/nestvault:latest
```

### Docker Compose

```yaml
services:
  # Your database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydb

  # NestVault backup service
  nestvault:
    image: ghcr.io/forgenest-services/nestvault:latest
    environment:
      # Database
      DATABASE_TYPE: postgres
      PG_HOST: postgres
      PG_PORT: 5432
      PG_DATABASE: mydb
      PG_USER: myuser
      PG_PASSWORD: mypassword

      # Storage (AWS S3)
      STORAGE_TYPE: s3
      S3_ACCESS_KEY: ${AWS_ACCESS_KEY_ID}
      S3_SECRET_KEY: ${AWS_SECRET_ACCESS_KEY}
      S3_BUCKET: my-backups
      S3_REGION: us-east-1

      # Schedule
      BACKUP_SCHEDULE: "0 */6 * * *"  # Every 6 hours
      RETENTION_DAYS: 7
```

## Examples

See the [examples](./examples) directory for complete working examples:

| Example | Stack | Database | Storage |
|---------|-------|----------|---------|
| [fastapi-postgres-s3](./examples/fastapi-postgres-s3) | FastAPI (Python) | PostgreSQL | AWS S3 |
| [express-mongodb-backblaze](./examples/express-mongodb-backblaze) | Express.js (Node.js) | MongoDB | Backblaze B2 |
| [go-postgres-r2](./examples/go-postgres-r2) | Go (Gin) | PostgreSQL | Cloudflare R2 |

## Configuration

All configuration is done via environment variables.

### Required Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_TYPE` | `postgres` or `mongodb` |
| `STORAGE_TYPE` | `s3`, `r2`, or `backblaze` |
| `BACKUP_SCHEDULE` | Cron expression (UTC timezone) |
| `RETENTION_DAYS` | Number of days to keep backups |

### PostgreSQL

| Variable | Description | Default |
|----------|-------------|---------|
| `PG_HOST` | Database host | Required |
| `PG_PORT` | Database port | `5432` |
| `PG_DATABASE` | Database name | Required |
| `PG_USER` | Username | Required |
| `PG_PASSWORD` | Password | Required |

### MongoDB

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | Connection URI (e.g., `mongodb://user:pass@host:27017/?authSource=admin`) |
| `MONGO_DATABASE` | Database name to backup |

### AWS S3

| Variable | Description |
|----------|-------------|
| `S3_ACCESS_KEY` | AWS Access Key ID |
| `S3_SECRET_KEY` | AWS Secret Access Key |
| `S3_BUCKET` | Bucket name |
| `S3_REGION` | AWS region (e.g., `us-east-1`) |

### Cloudflare R2

| Variable | Description |
|----------|-------------|
| `S3_ACCESS_KEY` | R2 Access Key ID |
| `S3_SECRET_KEY` | R2 Secret Access Key |
| `S3_BUCKET` | Bucket name |
| `S3_REGION` | `auto` |
| `S3_ENDPOINT` | R2 endpoint URL (required) |

### Backblaze B2

| Variable | Description |
|----------|-------------|
| `B2_KEY_ID` | Application Key ID |
| `B2_APPLICATION_KEY` | Application Key |
| `B2_BUCKET` | Bucket name |
| `B2_REGION` | B2 region (e.g., `us-east-005`) |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

## Backup Schedule Examples

| Expression | Description |
|------------|-------------|
| `0 * * * *` | Every hour |
| `0 */6 * * *` | Every 6 hours |
| `0 0 * * *` | Daily at midnight |
| `0 0 * * 0` | Weekly on Sunday |
| `0 0 1 * *` | Monthly on the 1st |

## Backup Naming

Backups are named using the format:
```
{database}_{YYYYMMDD}_{HHMMSS}.{extension}
```

| Database | Extension | Example |
|----------|-----------|---------|
| PostgreSQL | `.sql.gz` | `mydb_20240115_120000.sql.gz` |
| MongoDB | `.archive.gz` | `mydb_20240115_120000.archive.gz` |

## How It Works

1. **Startup**: NestVault runs an immediate backup on container start
2. **Scheduling**: Waits for the next scheduled time based on cron expression
3. **Backup**: Creates a compressed database dump using native tools (`pg_dump`/`mongodump`)
4. **Upload**: Uploads the backup to your configured storage backend
5. **Cleanup**: Deletes backups older than `RETENTION_DAYS`
6. **Repeat**: Waits for the next scheduled backup

## Restoring Backups

NestVault supports restoring backups when migrating to a new server or recovering from data loss.

### List Available Backups

```bash
docker run --rm \
  -e DATABASE_TYPE=postgres \
  -e PG_HOST=your-db-host \
  -e PG_PORT=5432 \
  -e PG_DATABASE=mydb \
  -e PG_USER=myuser \
  -e PG_PASSWORD=mypassword \
  -e STORAGE_TYPE=s3 \
  -e S3_ACCESS_KEY=${AWS_ACCESS_KEY_ID} \
  -e S3_SECRET_KEY=${AWS_SECRET_ACCESS_KEY} \
  -e S3_BUCKET=my-backups \
  -e S3_REGION=us-east-1 \
  -e BACKUP_SCHEDULE="0 0 * * *" \
  -e RETENTION_DAYS=7 \
  ghcr.io/forgenest-services/nestvault:latest restore --list
```

### Restore Latest Backup

```bash
docker run --rm \
  -e DATABASE_TYPE=postgres \
  -e PG_HOST=your-db-host \
  -e PG_PORT=5432 \
  -e PG_DATABASE=mydb \
  -e PG_USER=myuser \
  -e PG_PASSWORD=mypassword \
  -e STORAGE_TYPE=s3 \
  -e S3_ACCESS_KEY=${AWS_ACCESS_KEY_ID} \
  -e S3_SECRET_KEY=${AWS_SECRET_ACCESS_KEY} \
  -e S3_BUCKET=my-backups \
  -e S3_REGION=us-east-1 \
  -e BACKUP_SCHEDULE="0 0 * * *" \
  -e RETENTION_DAYS=7 \
  ghcr.io/forgenest-services/nestvault:latest restore
```

### Restore Specific Backup

```bash
docker run --rm \
  -e DATABASE_TYPE=postgres \
  -e PG_HOST=your-db-host \
  -e PG_PORT=5432 \
  -e PG_DATABASE=mydb \
  -e PG_USER=myuser \
  -e PG_PASSWORD=mypassword \
  -e STORAGE_TYPE=s3 \
  -e S3_ACCESS_KEY=${AWS_ACCESS_KEY_ID} \
  -e S3_SECRET_KEY=${AWS_SECRET_ACCESS_KEY} \
  -e S3_BUCKET=my-backups \
  -e S3_REGION=us-east-1 \
  -e BACKUP_SCHEDULE="0 0 * * *" \
  -e RETENTION_DAYS=7 \
  ghcr.io/forgenest-services/nestvault:latest restore --backup mydb_20240115_120000.sql.gz
```

### Restore Commands

| Command | Description |
|---------|-------------|
| `restore --list` | List all available backups |
| `restore` | Restore the most recent backup |
| `restore --backup <filename>` | Restore a specific backup file |

## Development

### Setup

```bash
git clone https://github.com/ForgeNest-services/nestvault.git
cd nestvault

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Building Docker Image

```bash
docker build -t nestvault .
```

## Architecture

```
nestvault/
├── backup/
│   ├── base.py       # Abstract backup interface
│   ├── postgres.py   # PostgreSQL adapter (pg_dump/psql)
│   └── mongodb.py    # MongoDB adapter (mongodump/mongorestore)
├── storage/
│   ├── base.py       # Abstract storage interface
│   ├── s3.py         # S3/R2 adapter (boto3)
│   └── backblaze.py  # Backblaze B2 adapter (b2sdk)
├── cli.py            # Command line argument parsing
├── config.py         # Environment configuration
├── scheduler.py      # Cron-based scheduler
├── retention.py      # Backup retention logic
├── restore.py        # Backup restore functionality
├── logging.py        # Structured logging (loguru)
└── main.py           # Entry point
```

## License

MIT
