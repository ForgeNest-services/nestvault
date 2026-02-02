# NestVault Examples

Complete working examples demonstrating NestVault integration with different tech stacks, databases, and storage backends.

## Available Examples

| Example | Application | Database | Storage | Port |
|---------|-------------|----------|---------|------|
| [fastapi-postgres-s3](./fastapi-postgres-s3) | FastAPI (Python) | PostgreSQL | AWS S3 | 8000 |
| [express-mongodb-backblaze](./express-mongodb-backblaze) | Express.js (Node.js) | MongoDB | Backblaze B2 | 3000 |
| [go-postgres-r2](./go-postgres-r2) | Go (Gin) | PostgreSQL | Cloudflare R2 | 8080 |

## Quick Start

Each example follows the same pattern:

```bash
# 1. Navigate to the example
cd <example-directory>

# 2. Copy the environment template and add your credentials
cp .env.tmpl .env

# 3. Edit .env with your storage credentials
#    (database credentials can use defaults for testing)

# 4. Start all services
docker-compose up -d

# 5. Verify NestVault is running
docker-compose logs -f nestvault
```

## What's Included

Each example contains:

```
example/
├── .env.tmpl          # Environment template (copy to .env)
├── .gitignore         # Ignores .env file
├── docker-compose.yml # Complete stack configuration
├── README.md          # Example-specific documentation
└── app/               # Sample application
    ├── Dockerfile
    └── ... (app code)
```

## Example Output

When NestVault starts successfully, you'll see logs like:

```
[2026-02-02T12:45:57.541Z] [INFO] [main] NestVault starting
[2026-02-02T12:45:57.541Z] [INFO] [main] Database type: postgres
[2026-02-02T12:45:57.541Z] [INFO] [main] Storage type: s3
[2026-02-02T12:45:57.727Z] [INFO] [scheduler] Starting scheduler with schedule: 0 */6 * * *
[2026-02-02T12:45:57.727Z] [INFO] [scheduler] Retention policy: 7 days
[2026-02-02T12:45:57.727Z] [INFO] [scheduler] Running initial backup
[2026-02-02T12:45:57.854Z] [INFO] [backup.postgres] Backup completed: tododb_20260202_124557.sql.gz (851 bytes)
[2026-02-02T12:45:59.227Z] [INFO] [storage.s3] Upload completed: tododb_20260202_124557.sql.gz
[2026-02-02T12:45:59.562Z] [INFO] [scheduler] Backup job completed successfully
[2026-02-02T12:45:59.562Z] [INFO] [scheduler] Next backup scheduled for: 2026-02-02T18:00:00+00:00
```

## Storage Provider Setup

### AWS S3
1. Create an S3 bucket
2. Create an IAM user with S3 access
3. Get Access Key ID and Secret Access Key

### Cloudflare R2
1. Create an R2 bucket in Cloudflare Dashboard
2. Create an R2 API Token with **Object Read & Write** permission
3. Get Access Key ID, Secret Access Key, and endpoint URL

### Backblaze B2
1. Create a B2 bucket
2. Create an Application Key with read/write access to the bucket
3. Get Key ID and Application Key

## Common Commands

```bash
# Start all services
docker-compose up -d

# View NestVault logs
docker-compose logs -f nestvault

# Trigger immediate backup (restarts container)
docker-compose restart nestvault

# Stop all services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

## Customization

### Change Backup Schedule

Edit `.env` and modify `BACKUP_SCHEDULE`:

```bash
# Every hour
BACKUP_SCHEDULE=0 * * * *

# Every 6 hours
BACKUP_SCHEDULE=0 */6 * * *

# Daily at midnight
BACKUP_SCHEDULE=0 0 * * *

# Daily at 3 AM
BACKUP_SCHEDULE=0 3 * * *
```

### Change Retention Period

Edit `.env` and modify `RETENTION_DAYS`:

```bash
# Keep backups for 30 days
RETENTION_DAYS=30
```

## Troubleshooting

### Backup fails with "Access Denied"
- Check that your storage credentials have write permissions
- For R2: Ensure the API token has "Object Read & Write" permission

### MongoDB authentication fails
- Ensure `?authSource=admin` is in the `MONGO_URI`
- Example: `mongodb://user:pass@host:27017/?authSource=admin`

### Container keeps restarting
- Check logs: `docker-compose logs nestvault`
- Verify all required environment variables are set
