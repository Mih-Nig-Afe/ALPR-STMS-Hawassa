FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/services/api:/workspace/services/worker:/workspace/packages/shared

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock pyproject.toml alembic.ini ./
RUN pip install --no-cache-dir -r requirements.lock

COPY services/api ./services/api
COPY services/worker ./services/worker
COPY packages ./packages
COPY infra/database ./infra/database
COPY data/seed ./data/seed

CMD ["./services/worker/bin/start-worker.sh"]

