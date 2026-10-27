# Lean Flask API image for ShipTrack AI (demo mode).
FROM python:3.13-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY backend/ /app/backend/
COPY docker/backend-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]
