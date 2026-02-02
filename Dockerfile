FROM python:3.12-slim

LABEL maintainer="NestVault Authors"
LABEL description="Container-native backup utility for PostgreSQL and MongoDB"

# Install database client tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gnupg \
    curl \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    mongodb-database-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash nestvault

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY nestvault/ ./nestvault/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER nestvault

# Run the application
CMD ["nestvault"]
