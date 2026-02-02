# Express.js + MongoDB + Backblaze B2 Example

This example demonstrates how to use **NestVault** to automatically backup a MongoDB database used by an Express.js application to Backblaze B2.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Express.js │────▶│   MongoDB   │◀────│  NestVault  │
│   (Todo)    │     │             │     │   Backup    │
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
# 1. Copy the environment template
cp .env.tmpl .env

# 2. Edit .env with your credentials
#    - Set your Backblaze B2 credentials
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
MONGO_ROOT_USER=appuser
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_DATABASE=tododb

# Backblaze B2 Configuration
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET=your_bucket_name
B2_REGION=us-east-005

# NestVault Configuration
BACKUP_SCHEDULE=0 */6 * * *   # Every 6 hours
RETENTION_DAYS=7               # Keep backups for 7 days
LOG_LEVEL=INFO
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 3000 | Express.js Todo application |
| mongodb | 27017 | MongoDB database |
| nestvault | - | Automated backup service |

## API Endpoints

- `GET /` - Health check
- `GET /todos` - List all todos
- `POST /todos` - Create a todo
- `GET /todos/:id` - Get a todo
- `PUT /todos/:id` - Update a todo
- `DELETE /todos/:id` - Delete a todo

## Test the API

```bash
# Create a todo
curl -X POST http://localhost:3000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn NestVault", "completed": false}'

# List todos
curl http://localhost:3000/todos
```

## Backup Schedule

NestVault is configured to:
- Backup every 6 hours (`0 */6 * * *`)
- Retain backups for 7 days

Backups are stored in your Backblaze B2 bucket with naming format:
```
tododb_20240115_120000.archive.gz
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
