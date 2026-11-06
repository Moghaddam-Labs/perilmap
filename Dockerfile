FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PERILMAP_DATA_DIR=/app/grids

WORKDIR /app

# The data packages need these system libraries, and the slim image may leave some out.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 libstdc++6 zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.api.lock .
RUN pip install --no-cache-dir -r requirements.api.lock

COPY perilmap ./perilmap
COPY grids ./grids

RUN useradd --create-home --uid 10001 perilmap
USER perilmap

# One worker, because rate limits are held in memory. Access logs stay off for privacy.
# The app decides which forwarded address to trust, so the server mustn't apply its own rule.
CMD ["sh", "-c", "exec uvicorn perilmap.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log --no-server-header --no-proxy-headers"]
