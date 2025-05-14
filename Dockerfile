FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libzbar0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create wait-for-db script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
host="$1"\n\
shift\n\
cmd="$@"\n\
\n\
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "postgres" -c "\\q"; do\n\
  >&2 echo "Postgres is unavailable - sleeping"\n\
  sleep 1\n\
done\n\
\n\
>&2 echo "Postgres is up - executing command"\n\
exec $cmd' > /app/wait-for-db.sh && chmod +x /app/wait-for-db.sh

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p static/images

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
\n\
# Apply database migrations\n\
python -m alembic upgrade head\n\
\n\
# Start the application\n\
exec gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run with gunicorn for production
CMD ["./start.sh"] 