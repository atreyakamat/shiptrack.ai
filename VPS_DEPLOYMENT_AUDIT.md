# ShipTrack AI - VPS Deployment Audit

**Date:** 2025-08-11  
**Commit:** RC2 Stabilization (frozen)  
**Auditor:** Automated Infrastructure Audit

---

## 1. Current Architecture

### High-Level Overview
```
Internet → Nginx (Port 80/443) → Frontend (Streamlit, Port 8501) + Backend API (Flask/Gunicorn, Port 5000)
                                          ↓
                                    PostgreSQL (Port 5432, internal only)
```

### Component Architecture
| Component | Technology | Port | Public Exposure |
|-----------|------------|------|-----------------|
| Reverse Proxy | Nginx (Alpine) | 80, 443 | **YES** (Only public entry) |
| Frontend | Streamlit | 8501 | NO (via Nginx) |
| Backend API | Flask + Gunicorn | 5000 | NO (via Nginx /api) |
| Scheduler | APScheduler (BackgroundScheduler) | N/A | NO (internal) |
| Database | PostgreSQL 15 | 5432 | NO (internal Docker network) |
| File Storage | Local volume (`./uploads`) | N/A | NO |

---

## 2. Existing Docker Services

### docker-compose.yml Services (5 total)

| Service | Image/Build | Purpose | Health Check | Restart Policy |
|---------|-------------|---------|--------------|----------------|
| `nginx` | `nginx:alpine` | Reverse proxy, SSL termination | None | `unless-stopped` |
| `backend` | `docker/backend.Dockerfile` | Flask API (Gunicorn 4 workers) | Depends on db healthy | `unless-stopped` |
| `scheduler` | `docker/backend.Dockerfile` | Background refresh jobs | Depends on db healthy, backend started | `unless-stopped` |
| `frontend` | `docker/frontend.Dockerfile` | Streamlit UI | Depends on backend | `unless-stopped` |
| `db` | `postgres:15-alpine` | PostgreSQL database | `pg_isready` (10s interval, 5 retries) | `unless-stopped` |

### Dockerfile Analysis

#### Root `Dockerfile` (NOT USED by compose - appears legacy)
- **Base:** `python:3.13-slim`
- **Issue:** Runs both Flask (`flask run`) AND Streamlit in same container via shell script
- **Problem:** Not production-ready (development server, no process manager)
- **Status:** Should be removed or marked deprecated

#### `docker/backend.Dockerfile` (USED)
- **Base:** `python:3.9-slim`
- **System deps:** tesseract-ocr, libgl1-mesa-glx, libglib2.0-0 (for OCR)
- **Python deps:** From `backend/requirements.txt` + gunicorn + psycopg2-binary
- **Entrypoint:** Gunicorn with 4 workers, 120s timeout
- **Port:** 5000
- **Status:** Production-ready

#### `docker/frontend.Dockerfile` (USED)
- **Base:** `python:3.9-slim`
- **Python deps:** From `frontend/requirements.txt`
- **Copies:** Frontend code + `.streamlit/` config
- **Entrypoint:** `streamlit run` on port 8501
- **Port:** 8501
- **Status:** Production-ready (Streamlit handles its own production serving)

---

## 3. Required Environment Variables

### From `.env.production.example` + Code Analysis

| Variable | Required | Default | Purpose | Source |
|----------|----------|---------|---------|--------|
| `FLASK_ENV` | Yes | - | Flask config mode | `config.py` |
| `SECRET_KEY` | **YES** | - | JWT signing, sessions | `config.py` |
| `DATABASE_URL` | Yes | `sqlite:///shiptrack.db` | DB connection string | `config.py` |
| `ADMIN_EMAIL` | **YES** (prod) | - | Initial admin user | `app.py:seed_db()` |
| `ADMIN_PASSWORD` | **YES** (prod) | - | Initial admin password | `app.py:seed_db()` |
| `TRACKING_PROVIDER` | No | `mock` | Carrier adapter selection | `config.py` |
| `TRACKING_DEMO_MODE` | No | `true` | Enable mock data fallback | `config.py` |
| `AI_PROVIDER` | No | `mock` | AI backend selection | `config.py` |
| `AI_API_KEY` | No | `` | OpenAI/Ollama API key | `config.py` |
| `AI_MODEL` | No | `gpt-3.5-turbo` | Model name | `config.py` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama endpoint | `config.py` |
| `OCR_ENGINE` | No | `easyocr` | OCR backend | `config.py` |
| `OCR_DEMO_MODE` | No | `true` | Mock OCR fallback | `config.py` |
| `SCHEDULER_ENABLED` | No | `false` | Enable background jobs | `config.py` |
| `REFRESH_INTERVAL_MINUTES` | No | `60` | Scheduler interval | `config.py` |
| `WHATSAPP_*` | No | `` | WhatsApp notifications | `config.py` |
| `EMAIL_*` / `SMTP_*` | No | `` | Email notifications | `config.py` |
| `MAX_UPLOAD_SIZE_MB` | No | `16` | Upload limit | `config.py` |
| `UPLOAD_FOLDER` | No | `uploads` | File storage path | `config.py` |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity | `config.py` |
| `POSTGRES_USER` | Yes (compose) | `shiptrack` | DB username | `docker-compose.yml` |
| `POSTGRES_PASSWORD` | **YES** (compose) | - | DB password | `docker-compose.yml` |
| `POSTGRES_DB` | Yes (compose) | `shiptrack` | DB name | `docker-compose.yml` |

### Missing from `.env.production.example` but used in code:
- `SECRET_KEY` - critical for JWT
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` - required for production bootstrap
- `POSTGRES_PASSWORD` - required for DB

---

## 4. Required Ports

| Port | Service | Protocol | Exposure | Notes |
|------|---------|----------|----------|-------|
| **80** | Nginx | HTTP | **PUBLIC** | Redirect to HTTPS |
| **443** | Nginx | HTTPS | **PUBLIC** | Main entry point |
| **5000** | Backend (Gunicorn) | HTTP | Internal only | Nginx proxies `/api/*` |
| **8501** | Frontend (Streamlit) | HTTP/WS | Internal only | Nginx proxies `/` + WebSocket |
| **5432** | PostgreSQL | TCP | Internal only | Docker network only |

### Firewall Rules (UFW)
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5000       # Block direct backend
ufw deny 8501       # Block direct frontend
ufw deny 5432       # Block direct database
```

---

## 5. Persistent Volumes

| Volume | Mount Point | Purpose | Backup Strategy |
|--------|-------------|---------|-----------------|
| `pgdata` (named) | `/var/lib/postgresql/data` | PostgreSQL data | `pg_dump` (see BACKUP_RESTORE.md) |
| `./uploads` (bind) | `/app/uploads` | OCR documents, temp files | `tar` archive (see BACKUP_RESTORE.md) |

### Volume Concerns
- `./uploads` is a **bind mount** to host - survives container recreation but not VPS destruction
- `pgdata` is a **named Docker volume** - managed by Docker, survives container recreation
- Neither is automatically backed up to off-site storage

---

## 6. Database Requirements

### PostgreSQL Configuration
- **Version:** 15 (Alpine)
- **User:** `shiptrack` (from `POSTGRES_USER`)
- **Database:** `shiptrack` (from `POSTGRES_DB`)
- **Password:** From `POSTGRES_PASSWORD` env var (REQUIRED, no default in compose)
- **Connection String:** `postgresql://shiptrack:${POSTGRES_PASSWORD}@db:5432/shiptrack`

### Migration System
- **Tool:** Flask-Migrate (Alembic)
- **Config:** `migrations/env.py` - uses Flask app context
- **Command:** `flask db upgrade` (run inside backend container)
- **Models:** User, Shipment, TrackingEvent, OCRDocument, AISummary, Notification, NotificationPreference, RefreshLog, PostalOffice

### ⚠️ CRITICAL: No Migrations Exist
The `migrations/versions/` directory is **empty**. This means:
- `flask db migrate` has never been run
- Database schema will be created via `db.create_all()` on first run
- **Production will need initial migration generated and applied**

### Production Database State
- **MUST start EMPTY** (no demo data)
- Migrations create schema only
- Admin user created by `seed_db()` on first backend startup (if `ADMIN_EMAIL`/`ADMIN_PASSWORD` set)
- **DO NOT run `seed.py` in production** - creates demo shipments

---

## 7. Scheduler Requirements

### Current Implementation
- **File:** `backend/scheduler.py`
- **Library:** APScheduler `BackgroundScheduler`
- **Job:** `refresh_shipments_job` - calls `TrackingService.refresh_shipment()` for all active shipments
- **Interval:** `REFRESH_INTERVAL_MINUTES` (default 60) with 60s jitter
- **Trigger:** `IntervalTrigger`

### Deployment Architecture
- **Runs in separate container:** `scheduler` service
- **Uses same image as backend:** `docker/backend.Dockerfile`
- **Command override:** `["python", "backend/scheduler.py"]`
- **Dependencies:** Waits for `db` healthy + `backend` started
- **Single instance:** Only one scheduler container (prevents duplicate jobs)

### Critical Requirements
- Must NOT run inside Gunicorn workers (separate process)
- Must share same database connection pool config
- Requires `SCHEDULER_ENABLED=true` in environment

---

## 8. Reverse Proxy Requirements

### Nginx Configuration (`docker/nginx.conf`)

#### Current HTTP Server (Port 80) - Redirects to HTTPS
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN;

    # ACME challenge location for Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files $uri =404;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}
```

#### HTTPS Server (Port 443) - Production Entry Point
```nginx
server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN;

    # SSL Certificate paths (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem;

    # Strong SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; frame-ancestors 'self';" always;

    # Client body size for file uploads (OCR)
    client_max_body_size 16M;

    # Proxy timeouts
    proxy_read_timeout 120s;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Frontend (Streamlit) - WebSocket support required
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache off;
        proxy_buffering off;
    }

    # Health check endpoint (no auth, minimal logging)
    location /health {
        proxy_pass http://backend/api/health;
        access_log off;
    }
}
```

### ⚠️ Domain Placeholder
- **YOUR_DOMAIN** must be replaced with actual domain before deployment
- SSL certificate paths reference Let's Encrypt standard locations

---

## 9. SSL Requirements

### Current State
- **Nginx config:** Complete with placeholders
- **Certificates:** Not present (require domain + VPS)
- **Certbot:** Not configured
- **Auto-renewal:** Not configured

### Requirements for Production
1. **Domain name** pointing to VPS IP (A/AAAA record)
2. **Port 80 accessible** for ACME HTTP-01 challenge
3. **Certbot** installed on host or in separate container
4. **Certificate paths** mounted into Nginx container
5. **Cron/systemd timer** for auto-renewal (every 60 days)
6. **Post-renewal hook** to reload Nginx: `nginx -s reload`

### Recommended Certbot Setup
```bash
# On VPS host (not in container)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
# Or with nginx plugin if nginx runs on host
sudo certbot --nginx -d yourdomain.com
```

---

## 10. Remaining Infrastructure Blockers

### 🔴 Critical (Must Resolve Before Production)

| Blocker | Description | Impact | Resolution |
|---------|-------------|--------|------------|
| **No VPS Access** | No SSH credentials/IP for target server | Cannot deploy | User must provide VPS access |
| **No Domain Name** | No registered domain for SSL | No HTTPS, no production URL | User must provide domain + DNS |
| **No SSL Certificates** | Certbot needs domain + port 80 | Browser warnings, no HTTPS | Requires domain + VPS |
| **Hardcoded DB Password** | `docker-compose.yml` uses `${POSTGRES_PASSWORD}` but no default | Compose fails without env | Must set in `.env` |
| **No Production `.env`** | `.env` currently has SQLite + weak secrets | Insecure, wrong DB | Create from `.env.production.example` |
| **No Migrations** | `migrations/versions/` empty - never generated | Schema via `db.create_all()` only | Must run `flask db migrate` + `upgrade` |

### 🟡 High Priority (Should Fix Before Go-Live)

| Blocker | Description | Impact |
|---------|-------------|--------|
| **Legacy Root `Dockerfile`** | Confusing, runs dev servers | Remove or rename |
| **No Log Rotation** | Docker json-file driver unbounded | Disk exhaustion risk |
| **No Backup Automation** | Manual `pg_dump` only | Data loss risk |
| **No Monitoring** | No health dashboards/alerts | Blind to failures |
| **Streamlit Config** | No `.streamlit/config.toml` for production | May leak config, no headless tuning |

### 🟢 Medium Priority (Post-Launch)

| Blocker | Description |
|---------|-------------|
| **Rate Limiting** | Flask-Limiter uses in-memory (not shared across workers) |
| **Session Storage** | Flask sessions in signed cookies (OK for stateless) |
| **OCR Temp Files** | Cleanup on error paths needs verification |
| **Database Connection Pool** | Default SQLAlchemy pool may need tuning for 4 Gunicorn workers |

---

## 11. Security Audit Summary

| Area | Status | Notes |
|------|--------|-------|
| **JWT Secret** | ⚠️ Weak in `.env` | Must generate 32+ char random string |
| **Admin Password** | ⚠️ Weak in `.env` | Must use strong password |
| **DB Password** | ⚠️ Required but not set | Compose will fail |
| **Debug Mode** | ✅ Disabled in prod config | `ProductionConfig.DEBUG = False` |
| **Internal Ports** | ✅ Not exposed | Only Nginx ports 80/443 public |
| **Multi-tenant Isolation** | ✅ Enforced at API layer | User-scoped queries |
| **Rate Limiting** | ⚠️ In-memory only | Not shared across Gunicorn workers |
| **File Uploads** | ✅ Size limited (16MB) | Stored in non-public volume |
| **CORS** | ✅ Configured | Flask-CORS on backend |
| **Security Headers** | ✅ Complete in Nginx | HSTS, CSP, etc. configured |

---

## 12. Deployment Readiness Checklist

### Pre-Deployment (User Action Required)
- [ ] Provision VPS (Ubuntu 22.04+ recommended, 2GB+ RAM, 20GB+ disk)
- [ ] Configure SSH key access
- [ ] Register domain name, create A record → VPS IP
- [ ] Generate production secrets (SECRET_KEY, ADMIN_PASSWORD, POSTGRES_PASSWORD)
- [ ] Create `.env` from `.env.production.example` with real values

### Deployment Steps (Automated via Runbook)
- [ ] Clone repo at RC2 commit
- [ ] Configure `.env`
- [ ] `docker compose build`
- [ ] `docker compose up -d db` → wait for healthy
- [ ] `docker compose run --rm backend flask db migrate -m "Initial migration"` → generates migration
- [ ] `docker compose run --rm backend flask db upgrade` → applies migration
- [ ] `docker compose up -d backend scheduler frontend nginx`
- [ ] Verify `/api/health` returns 200
- [ ] Run Certbot for SSL
- [ ] Update Nginx config for HTTPS + reload
- [ ] Test full application flow

### Post-Deployment Verification
- [ ] HTTPS works, HTTP redirects
- [ ] Login with ADMIN_EMAIL works
- [ ] Dashboard loads, shipments list works
- [ ] Shipment detail renders (no raw HTML, no None values)
- [ ] OCR upload works
- [ ] AI insights generate
- [ ] Scheduler runs (check logs)
- [ ] Backup/restore tested
- [ ] Reboot test passes

---

## 13. File Inventory for Deployment

### Must Deploy to VPS
```
/opt/shiptrack-ai/
├── docker-compose.yml
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
├── backend/
├── frontend/
├── migrations/
├── requirements.txt
├── run.py
├── seed.py (for reference only - DO NOT RUN IN PROD)
├── .env (created on VPS, NOT committed)
├── .git/ (for version tracking)
└── DEPLOYMENT_VERSION (commit SHA)
```

### Must NOT Deploy / Must Be Excluded
- `.env.local`, `.env` (local development)
- `instance/` (SQLite dev database)
- `uploads/` (will be created by container)
- `__pycache__/`, `.pytest_cache/`
- `tests/` (not needed in production)
- `venv/`, `.venv/`

---

*End of VPS Deployment Audit*