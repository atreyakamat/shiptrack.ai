# ShipTrack AI - Production Runbook

**Version:** RC2 (commit `2dd365a6dabadff11d5e0c7eb45694ca618f247e`)  
**Environment:** Production (Docker Compose)  
**Last Updated:** 2025-08-11

---

## 🚀 START - Start All Services

```bash
cd /opt/shiptrack-ai
docker compose up -d
```

**Expected:** All 5 containers (db, backend, scheduler, frontend, nginx) show `Up` status with health checks passing.

---

## 🛑 STOP - Stop All Services

### Graceful Stop (preserves state)
```bash
docker compose stop
```

### Stop and Remove Containers (preserves volumes)
```bash
docker compose down
```

### Full Cleanup (⚠️ DESTROYS DATA - includes volumes)
```bash
docker compose down -v
```

---

## 🔄 RESTART - Restart Services

### Restart Specific Service
```bash
docker compose restart backend
docker compose restart frontend
docker compose restart scheduler
docker compose restart nginx
docker compose restart db
```

### Restart Entire Stack
```bash
docker compose restart
```

### Rebuild and Restart (after code changes)
```bash
docker compose build
docker compose up -d
```

---

## 📋 LOGS - View Logs

### All Services (follow, last 100 lines)
```bash
docker compose logs --tail=100 -f
```

### Specific Service
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f scheduler
docker compose logs -f nginx
docker compose logs -f db
```

### Last N Lines (non-follow)
```bash
docker compose logs --tail=200 backend
```

### Since Timestamp
```bash
docker compose logs --since="2025-08-11T10:00:00" backend
```

---

## 🏥 HEALTH CHECK - Verify Service Health

### Container Health Status
```bash
docker compose ps
```
**Look for:** `(healthy)` under STATUS for `db` container.

### Application Health Endpoints
```bash
# Backend API health (via Nginx)
curl -f http://localhost/api/health
# Expected: {"status":"ok","version":"1.0.0","demo_mode":false,"tracking_provider":"mock","ai_provider":"mock"}

# Backend direct (internal)
docker compose exec backend curl -f http://localhost:5000/api/health

# Frontend (via Nginx)
curl -f http://localhost/
# Should return Streamlit HTML

# Database connectivity
docker compose exec db pg_isready -U shiptrack
```

### Scheduler Health
```bash
docker compose logs scheduler | grep -E "(Starting scheduler|Finished background refresh|Error)"
```
**Expected:** Periodic "Starting background refresh job..." and "Finished background refresh job." messages.

---

## 🗄️ DATABASE - Database Operations

### Run Migrations
```bash
docker compose run --rm backend flask db upgrade
```

### Create New Migration (after model changes)
```bash
docker compose run --rm backend flask db migrate -m "description of changes"
```

### Show Migration History
```bash
docker compose run --rm backend flask db history
```

### Current Migration Revision
```bash
docker compose run --rm backend flask db current
```

### Rollback Migration (⚠️ CAREFUL)
```bash
docker compose run --rm backend flask db downgrade <revision>
```

### Database Shell
```bash
docker compose exec db psql -U shiptrack -d shiptrack
```

### Verify Tables
```bash
docker compose exec db psql -U shiptrack -d shiptrack -c "\dt"
```

### Count Records (sanity check)
```bash
docker compose exec db psql -U shiptrack -d shiptrack -c "SELECT COUNT(*) FROM shipment;"
docker compose exec db psql -U shiptrack -d shiptrack -c "SELECT COUNT(*) FROM tracking_event;"
docker compose exec db psql -U shiptrack -d shiptrack -c "SELECT COUNT(*) FROM \"user\";"
```

---

## 🔐 ADMIN - Admin User Management

### Create Admin User (if not auto-created)
```bash
docker compose run --rm backend python -c "
from backend.app import create_app
from backend.models.user import User
from backend.extensions import db
from werkzeug.security import generate_password_hash
import os
app = create_app()
with app.app_context():
    email = os.getenv('ADMIN_EMAIL')
    pwd = os.getenv('ADMIN_PASSWORD')
    if User.query.filter_by(email=email).first() is None:
        u = User(email=email, password_hash=generate_password_hash(pwd))
        db.session.add(u)
        db.session.commit()
        print(f'Created admin: {email}')
    else:
        print('Admin already exists')
"
```

### Reset Admin Password
```bash
docker compose run --rm backend python -c "
from backend.app import create_app
from backend.models.user import User
from backend.extensions import db
from werkzeug.security import generate_password_hash
import os
app = create_app()
with app.app_context():
    email = os.getenv('ADMIN_EMAIL')
    new_pwd = input('New password: ')
    u = User.query.filter_by(email=email).first()
    if u:
        u.password_hash = generate_password_hash(new_pwd)
        db.session.commit()
        print('Password updated')
    else:
        print('User not found')
"
```

---

## 📦 BACKUP & RESTORE - See BACKUP_RESTORE.md

```bash
# Quick backup
./scripts/backup.sh

# Quick restore
./scripts/restore.sh <backup_file>
```

---

## 🔧 UPDATE - Deploy New Version

```bash
cd /opt/shiptrack-ai

# 1. Fetch latest
git fetch origin

# 2. Verify commit (check DEPLOYMENT_VERSION or git log)
git log --oneline -5

# 3. Checkout target commit (TAG or SHA)
git checkout <COMMIT_SHA_OR_TAG>

# 4. Record deployment version
git rev-parse HEAD > DEPLOYMENT_VERSION

# 5. Build and deploy
docker compose build
docker compose up -d

# 6. Run migrations if needed
docker compose run --rm backend flask db upgrade

# 7. Verify health
curl -f http://localhost/api/health
```

---

## 💾 MIGRATE - Database Migrations Only

```bash
# Run pending migrations
docker compose run --rm backend flask db upgrade

# Verify
docker compose run --rm backend flask db current
```

---

## 💽 DISK CHECK - Monitor Disk Usage

### Host Disk Usage
```bash
df -h
```

### Docker Disk Usage
```bash
docker system df
```

### Cleanup Unused Docker Objects (⚠️ DESTROYS UNUSED DATA)
```bash
# Remove stopped containers, unused networks, dangling images
docker system prune -f

# Aggressive: remove ALL unused images, build cache, volumes
docker system prune -a --volumes -f
```

### Check Specific Volumes
```bash
docker volume ls
docker volume inspect shiptrack-ai_pgdata
```

---

## 🐳 DOCKER CHECK - Container Health & Resources

### Container Status
```bash
docker compose ps
```

### Resource Usage (Live)
```bash
docker stats --no-stream
```

### Detailed Container Inspect
```bash
docker inspect shiptrack-ai-backend-1
docker inspect shiptrack-ai-db-1
```

### Network Inspection
```bash
docker network ls
docker network inspect shiptrack-ai_default
```

---

## 🔒 SECURITY CHECKS

### Verify No Secrets in Logs
```bash
docker compose logs backend | grep -iE "(password|secret|token|key)" || echo "No secrets found"
```

### Verify Internal Ports Not Exposed
```bash
# Should show ONLY nginx ports 80/443
ss -tulpn | grep -E "(80|443|5000|8501|5432)"
```

### Verify Firewall (UFW)
```bash
sudo ufw status verbose
```

### Check SSL Certificate Expiry
```bash
# If using Let's Encrypt
sudo certbot certificates
```

---

## 📊 MONITORING QUERIES

### Active Shipments Count
```bash
docker compose exec db psql -U shiptrack -d shiptrack -c "
SELECT status, COUNT(*) FROM shipment GROUP BY status;
"
```

### Recent Tracking Refreshes
```bash
docker compose exec db psql -U shiptrack -d shiptrack -c "
SELECT status, completed_at, events_found FROM refresh_log ORDER BY completed_at DESC LIMIT 10;
"
```

### Failed Refreshes
```bash
docker compose exec db psql -U shiptrack -d shiptrack -c "
SELECT * FROM refresh_log WHERE status = 'error' ORDER BY completed_at DESC LIMIT 10;
"
```

---

## 🚨 EMERGENCY PROCEDURES

### Backend Not Responding
```bash
# 1. Check logs
docker compose logs --tail=50 backend

# 2. Restart backend
docker compose restart backend

# 3. If DB connection issues, check DB
docker compose logs db
docker compose restart db
```

### Database Corruption / Won't Start
```bash
# 1. Check logs
docker compose logs db

# 2. Restore from backup (see BACKUP_RESTORE.md)
# DO NOT delete pgdata volume without backup!
```

### Out of Disk Space
```bash
# 1. Check
df -h
docker system df

# 2. Clean Docker
docker system prune -a --volumes -f

# 3. Clean old backups
ls -la /opt/shiptrack-ai/backups/
# Remove old backups manually
```

### SSL Certificate Expired
```bash
# 1. Renew
sudo certbot renew

# 2. Reload nginx
docker compose exec nginx nginx -s reload
```

---

## 📝 CHANGELOG

| Date | Version | Changes |
|------|---------|---------|
| 2025-08-11 | RC2 | Initial production runbook |

---

*Keep this runbook updated with every deployment. Commands must match actual deployed architecture.*