#!/bin/sh
set -e

echo "=== SmartCampus 360 Backend Container Initializing ==="

# 1. Wait for PostgreSQL availability
echo "Checking database connectivity..."
python -c "
import sys, time
from sqlalchemy import create_engine, text
from app.core.config import settings

retries = 30
engine = create_engine(settings.DATABASE_URL)
while retries > 0:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database connection established successfully.')
        sys.exit(0)
    except Exception as e:
        print(f'Waiting for database ({retries} attempts remaining)...')
        time.sleep(2)
        retries -= 1

print('Error: Could not connect to database after timeout.')
sys.exit(1)
"

# 2. Run Alembic database migrations
echo "Executing database migrations (alembic upgrade head)..."
python -m alembic upgrade head

# 3. Seed initial reference users and departments idempotently
echo "Seeding initial reference data..."
python -c "
import sys
from app.core.seed import seed_database
result = seed_database()
print(f'Seed status: {result[\"status\"]}, created users: {len(result[\"created_users\"])}')
" || echo "Notice: Database seeding already complete or skipped."

# 4. Start Uvicorn ASGI server
echo "Starting Uvicorn ASGI server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
