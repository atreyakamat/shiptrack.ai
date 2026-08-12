# ShipTrack AI - Backup & Restore Procedures

**Version:** RC2  
**Environment:** Production (Docker Compose)  
**Last Updated:** 2025-08-11

---

## 📋 Overview

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| PostgreSQL Database | `pg_dump` (custom format) | Daily | 30 days |
| Upload Files (`./uploads`) | `tar.gz` | Weekly | 8 weeks |
| Configuration (`.env`, `docker-compose.yml`) | Git / Manual copy | On change | Permanent |

**Storage Location:** `/opt/shiptrack-ai/backups/` on VPS host  
**Off-site Copy:** **REQUIRED** - Copy to S3, remote server, or local machine

---

## 1. DATABASE BACKUP

### Create Backup (Production Database)

```bash
cd /opt/shiptrack-ai

# Create backup directory if not exists
mkdir -p backups

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/db_backup_${TIMESTAMP}.dump"

# Run pg_dump from inside the database container
# -Fc = custom format (compressed, allows selective restore)
# -U = username, -d = database
docker exec -t shiptrack-ai-db-1 pg_dump -U shiptrack -d shiptrack -Fc -f /tmp/db_backup.dump

# Copy from container to host
docker cp shiptrack-ai-db-1:/tmp/db_backup.dump "${BACKUP_FILE}"

# Cleanup temp file in container
docker exec shiptrack-ai-db-1 rm /tmp/db_backup.dump

# Verify backup
ls -lh "${BACKUP_FILE}"
# Should be ~1-10MB depending on data

echo "Backup created: ${BACKUP_FILE}"
```

### Automated Daily Backup (Cron)

```bash
# Add to root crontab on VPS host
sudo crontab -e

# Add this line (runs at 2:30 AM daily):
30 2 * * * /opt/shiptrack-ai/scripts/backup_db.sh >> /var/log/shiptrack-backup.log 2>&1
```

**Create `/opt/shiptrack-ai/scripts/backup_db.sh`:**
```bash
#!/bin/bash
set -e

cd /opt/shiptrack-ai
mkdir -p backups

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/db_backup_${TIMESTAMP}.dump"

echo "[$(date)] Starting database backup..."

docker exec -t shiptrack-ai-db-1 pg_dump -U shiptrack -d shiptrack -Fc -f /tmp/db_backup.dump
docker cp shiptrack-ai-db-1:/tmp/db_backup.dump "${BACKUP_FILE}"
docker exec shiptrack-ai-db-1 rm /tmp/db_backup.dump

# Verify
if [ -f "${BACKUP_FILE}" ] && [ $(stat -c%s "${BACKUP_FILE}") -gt 1000 ]; then
    echo "[$(date)] Backup successful: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"
    
    # Optional: Remove backups older than 30 days
    find backups/db_backup_*.dump -mtime +30 -delete
    echo "[$(date)] Cleaned old backups"
else
    echo "[$(date)] ERROR: Backup failed or empty!"
    exit 1
fi
```

```bash
chmod +x /opt/shiptrack-ai/scripts/backup_db.sh
```

---

## 2. UPLOADS BACKUP

### Create Backup (OCR Documents & Temp Files)

```bash
cd /opt/shiptrack-ai

TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="backups/uploads_backup_${TIMESTAMP}.tar.gz"

# Exclude any lock files or temp files
tar -czvf "${BACKUP_FILE}" --exclude="*.lock" --exclude="*.tmp" uploads/

echo "Uploads backup created: ${BACKUP_FILE}"
ls -lh "${BACKUP_FILE}"
```

### Automated Weekly Backup (Cron)

```bash
# Add to crontab (runs Sunday 3:00 AM)
0 3 * * 0 /opt/shiptrack-ai/scripts/backup_uploads.sh >> /var/log/shiptrack-backup.log 2>&1
```

**Create `/opt/shiptrack-ai/scripts/backup_uploads.sh`:**
```bash
#!/bin/bash
set -e

cd /opt/shiptrack-ai
mkdir -p backups

TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="backups/uploads_backup_${TIMESTAMP}.tar.gz"

echo "[$(date)] Starting uploads backup..."

tar -czvf "${BACKUP_FILE}" --exclude="*.lock" --exclude="*.tmp" uploads/

if [ -f "${BACKUP_FILE}" ] && [ $(stat -c%s "${BACKUP_FILE}") -gt 1000 ]; then
    echo "[$(date)] Uploads backup successful: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"
    
    # Keep 8 weeks
    find backups/uploads_backup_*.tar.gz -mtime +56 -delete
else
    echo "[$(date)] ERROR: Uploads backup failed!"
    exit 1
fi
```

```bash
chmod +x /opt/shiptrack-ai/scripts/backup_uploads.sh
```

---

## 3. CONFIGURATION BACKUP

### Manual Backup (Run After Any Config Change)

```bash
cd /opt/shiptrack-ai

# Backup .env (contains secrets - store securely!)
cp .env "backups/env_backup_$(date +%Y%m%d_%H%M%S)"

# Backup docker-compose.yml
cp docker-compose.yml "backups/docker-compose_backup_$(date +%Y%m%d_%H%M%S).yml"

# Backup nginx.conf
cp docker/nginx.conf "backups/nginx_backup_$(date +%Y%m%d_%H%M%S).conf"

# Git commit for version tracking
git add -A
git commit -m "Config backup: $(date +%Y-%m-%d)"
```

---

## 4. RESTORE PROCEDURES

### ⚠️ CRITICAL: Test Restore in Isolation First

**NEVER restore directly to production without verifying the backup first.**

### 4.1 Verify Backup Integrity (Test Restore)

```bash
cd /opt/shiptrack-ai

BACKUP_FILE="backups/db_backup_20250811_023000.dump"

# 1. Spin up temporary PostgreSQL container
docker run --name pg-verify \
    -e POSTGRES_PASSWORD=testverify \
    -e POSTGRES_USER=testverify \
    -e POSTGRES_DB=shiptrack \
    -d postgres:15-alpine

# 2. Wait for readiness
sleep 5
docker exec pg-verify pg_isready -U testverify

# 3. Copy backup into container
docker cp "${BACKUP_FILE}" pg-verify:/tmp/db_backup.dump

# 4. Restore
docker exec -t pg-verify pg_restore -U testverify -d shiptrack -1 /tmp/db_backup.dump

# 5. Verify data
docker exec pg-verify psql -U testverify -d shiptrack -c "SELECT COUNT(*) FROM shipment;"
docker exec pg-verify psql -U testverify -d shiptrack -c "SELECT COUNT(*) FROM tracking_event;"
docker exec pg-verify psql -U testverify -d shiptrack -c "SELECT COUNT(*) FROM \"user\";"

# 6. Cleanup
docker rm -f pg-verify

echo "Backup verification complete - backup is valid"
```

### 4.2 Restore to Production Database

```bash
cd /opt/shiptrack-ai

BACKUP_FILE="backups/db_backup_20250811_023000.dump"

echo "⚠️  PRODUCTION DATABASE RESTORE"
echo "This will DESTROY current data. Continue? (y/N)"
read -r CONFIRM
if [ "${CONFIRM}" != "y" ]; then
    echo "Aborted."
    exit 1
fi

# 1. Stop application services (keep DB running)
docker compose stop backend frontend scheduler nginx

# 2. Drop and recreate database (clean slate)
echo "Dropping and recreating database..."
docker exec -it shiptrack-ai-db-1 dropdb -U shiptrack shiptrack || true
docker exec -it shiptrack-ai-db-1 createdb -U shiptrack shiptrack

# 3. Copy backup into container
docker cp "${BACKUP_FILE}" shiptrack-ai-db-1:/tmp/db_backup.dump

# 4. Restore
# -1 = single transaction (all or nothing)
# -U = username, -d = database
docker exec -t shiptrack-ai-db-1 pg_restore -U shiptrack -d shiptrack -1 /tmp/db_backup.dump

# 5. Cleanup temp file
docker exec shiptrack-ai-db-1 rm /tmp/db_backup.dump

# 6. Run migrations (in case schema changed)
docker compose run --rm backend flask db upgrade

# 7. Restart all services
docker compose up -d

# 8. Verify
sleep 10
curl -f http://localhost/api/health
echo "Restore complete. Verify application manually."
```

### 4.3 Restore Uploads

```bash
cd /opt/shiptrack-ai

BACKUP_FILE="backups/uploads_backup_20250811.tar.gz"

echo "Restoring uploads from ${BACKUP_FILE}..."

# Stop services that might write to uploads
docker compose stop backend frontend scheduler

# Backup current uploads (just in case)
mv uploads "uploads.backup.$(date +%Y%m%d_%H%M%S)"

# Extract
tar -xzvf "${BACKUP_FILE}"

# Restart
docker compose up -d

echo "Uploads restored."
```

---

## 5. DISASTER RECOVERY (VPS Destroyed)

### Prerequisites (Must Have Before Disaster)
- [ ] `.env` file backed up securely (password manager, encrypted USB)
- [ ] Latest `db_backup_*.dump` copied off-site
- [ ] Latest `uploads_backup_*.tar.gz` copied off-site
- [ ] `docker-compose.yml` and `docker/nginx.conf` in Git
- [ ] This runbook accessible

### Recovery Steps on New VPS

```bash
# 1. Provision new VPS (Ubuntu 22.04+, 2GB+ RAM, 20GB+ disk)
# 2. Install Docker & Docker Compose
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# 3. Clone repository
git clone <your-repo-url> /opt/shiptrack-ai
cd /opt/shiptrack-ai

# 4. Checkout exact deployment commit
git checkout <COMMIT_SHA_FROM_DEPLOYMENT_VERSION>

# 5. Restore .env from secure backup
# (Copy from password manager/encrypted backup)
# Ensure POSTGRES_PASSWORD, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD match original

# 6. Start database only
docker compose up -d db

# 7. Wait for DB healthy
until docker compose exec db pg_isready -U shiptrack; do sleep 2; done

# 8. Restore database from off-site backup
# Copy backup file to VPS first (scp, s3 cp, etc.)
docker cp db_backup_latest.dump shiptrack-ai-db-1:/tmp/
docker exec -it shiptrack-ai-db-1 dropdb -U shiptrack shiptrack || true
docker exec -it shiptrack-ai-db-1 createdb -U shiptrack shiptrack
docker exec -t shiptrack-ai-db-1 pg_restore -U shiptrack -d shiptrack -1 /tmp/db_backup_latest.dump
docker exec shiptrack-ai-db-1 rm /tmp/db_backup_latest.dump

# 9. Restore uploads
tar -xzvf uploads_backup_latest.tar.gz

# 10. Run migrations
docker compose run --rm backend flask db upgrade

# 11. Start all services
docker compose up -d

# 12. Verify
curl -f http://localhost/api/health

# 13. Configure DNS → new VPS IP
# 14. Run Certbot for SSL
sudo certbot --nginx -d yourdomain.com

echo "Disaster recovery complete."
```

---

## 6. BACKUP VERIFICATION CHECKLIST

### Weekly (Automated via Cron)
- [ ] Database backup created successfully (check log)
- [ ] Backup file size > 1KB (not empty)
- [ ] Uploads backup created (if changed)

### Monthly (Manual)
- [ ] **Test restore** to isolated container (Section 4.1)
- [ ] Verify row counts match production
- [ ] Verify off-site copies exist and are readable
- [ ] Check backup directory disk usage

### Quarterly
- [ ] Full disaster recovery drill (Section 5) on test VPS
- [ ] Review and update retention policies
- [ ] Verify `.env` backup is current

---

## 7. BACKUP SCRIPTS SUMMARY

| Script | Purpose | Schedule |
|--------|---------|----------|
| `scripts/backup_db.sh` | PostgreSQL `pg_dump` | Daily 2:30 AM |
| `scripts/backup_uploads.sh` | Uploads `tar.gz` | Weekly Sunday 3:00 AM |
| `scripts/verify_backup.sh` | Test restore to temp DB | Monthly (manual) |

### Install Scripts

```bash
mkdir -p /opt/shiptrack-ai/scripts
# Copy backup_db.sh, backup_uploads.sh, verify_backup.sh to scripts/
chmod +x /opt/shiptrack-ai/scripts/*.sh

# Add to crontab
sudo crontab -e
# 30 2 * * * /opt/shiptrack-ai/scripts/backup_db.sh >> /var/log/shiptrack-backup.log 2>&1
# 0 3 * * 0 /opt/shiptrack-ai/scripts/backup_uploads.sh >> /var/log/shiptrack-backup.log 2>&1
```

---

## 8. TROUBLESHOOTING

| Issue | Resolution |
|-------|------------|
| `pg_dump: error: connection to server failed` | Check DB container running: `docker compose ps db` |
| `pg_restore: error: could not execute query` | Schema mismatch - run `flask db upgrade` after restore |
| `tar: uploads: Cannot stat: No such file or directory` | Create uploads dir: `mkdir -p uploads` |
| Backup file 0 bytes | Container not ready, check `docker compose logs db` |
| Off-site copy fails | Check SSH keys, S3 credentials, network connectivity |

---

## 9. CONTACT / ESCALATION

- **Primary:** DevOps / Platform Team
- **Backup:** Senior Backend Engineer
- **Emergency:** CTO / Technical Lead

---

*Last verified: 2025-08-11*  
*Next verification due: 2025-09-11*