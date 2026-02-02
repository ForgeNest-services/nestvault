# NestVault Examples

This directory contains example applications demonstrating NestVault integration with different tech stacks.

## Examples

| Example | Stack | Database | Storage |
|---------|-------|----------|---------|
| [fastapi-postgres-s3](./fastapi-postgres-s3) | FastAPI (Python) | PostgreSQL | AWS S3 |
| [express-mongodb-backblaze](./express-mongodb-backblaze) | Express.js (Node.js) | MongoDB | Backblaze B2 |

## Running Examples

Each example includes:
- `.env.tmpl` - Template for environment variables (copy to `.env`)
- `docker-compose.yml` - All services configured
- `app/` - Sample application code
- `README.md` - Setup instructions

```bash
cd <example-directory>
cp .env.tmpl .env
# Edit .env with your credentials
docker-compose up -d
```

## Structure

```
examples/
├── README.md
├── fastapi-postgres-s3/
│   ├── .env.tmpl
│   ├── .gitignore
│   ├── docker-compose.yml
│   ├── README.md
│   └── app/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
└── express-mongodb-backblaze/
    ├── .env.tmpl
    ├── .gitignore
    ├── docker-compose.yml
    ├── README.md
    └── app/
        ├── Dockerfile
        ├── index.js
        └── package.json
```
