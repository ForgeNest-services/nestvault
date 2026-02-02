# NestVault Examples

This directory contains example applications demonstrating NestVault integration with different tech stacks.

## Examples

| Example | Stack | Database | Storage |
|---------|-------|----------|---------|
| [fastapi-postgres-s3](./fastapi-postgres-s3) | FastAPI (Python) | PostgreSQL | S3 (MinIO) |

## Coming Soon

- `express-mongodb-s3` - Express.js + MongoDB + S3
- `fastapi-mongodb-backblaze` - FastAPI + MongoDB + Backblaze B2
- `express-postgres-r2` - Express.js + PostgreSQL + Cloudflare R2

## Running Examples

Each example includes a `docker-compose.yml` that starts:
- The application
- The database
- Storage backend (MinIO for local S3-compatible storage)
- NestVault for automated backups

```bash
cd <example-directory>
docker-compose up -d
```

## Structure

```
examples/
├── README.md
├── fastapi-postgres-s3/
│   ├── docker-compose.yml
│   ├── README.md
│   └── app/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
└── ...
```
