FROM python:3.12-slim

LABEL maintainer="NestVault Authors"
LABEL description="Container-native backup utility for PostgreSQL and MongoDB"

# Install database client tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && curl -fsSL https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-100.10.0.tgz \
    -o /tmp/mongodb-tools.tgz \
    && tar -xzf /tmp/mongodb-tools.tgz -C /tmp \
    && mv /tmp/mongodb-database-tools-*/bin/* /usr/local/bin/ \
    && rm -rf /tmp/mongodb-* \
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
