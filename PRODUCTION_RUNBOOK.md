# ShipTrack AI - Production Runbook

## Daily Operations

### START
To start the entire application stack in the background:
```bash
docker compose up -d
```

### STOP
To gracefully stop all application services:
```bash
docker compose stop
```

To stop and remove all containers (preserves volumes):
```bash
docker compose down
```

### RESTART
To restart a specific service (e.g., the backend):
```bash
docker compose restart backend
```
To restart the entire stack:
```bash
docker compose restart
```

### LOGS
To view logs for all services (tailing the last 100 lines and following):
```bash
docker compose logs --tail=100 -f
```
To view logs for a specific service (e.g., backend, frontend, scheduler, nginx, db):
```bash
docker compose logs -f scheduler
```

### HEALTH CHECK
To check the container health status of all running services:
```bash
docker ps
```
*(Look for `(healthy)` or `(unhealthy)` under the STATUS column for the `db` container).*

To check the application backend health directly:
```bash
curl -f http://localhost:5000/api/health
```

### BACKUP & RESTORE
Refer to `BACKUP_RESTORE.md` for exact commands to dump and restore the PostgreSQL database and upload volumes.

### ROLLBACK
Refer to `ROLLBACK.md` for exact commands on how to checkout an older git commit and safely revert the Docker environment.

### UPDATE (DEPLOYMENT)
To deploy a new commit to production:
1. Fetch and checkout the exact target commit.
2. Build and restart the containers:
```bash
git fetch
git checkout <COMMIT_SHA>
docker compose build
docker compose up -d
```

### MIGRATE
To run database migrations against the production database:
```bash
docker compose run --rm backend flask db upgrade
```

### DISK CHECK
To check disk usage on the VPS:
```bash
df -h
```
To check Docker-specific disk usage:
```bash
docker system df
```
If Docker is consuming too much space with unused images/containers, run (WARNING: destroys unused data):
```bash
docker system prune -a --volumes
```

### DOCKER CHECK
To list all active containers and their memory/CPU usage:
```bash
docker stats
```
