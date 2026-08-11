# ShipTrack AI - VPS Deployment Audit

## 1. Current Architecture
- **Nginx Reverse Proxy:** Acts as the main entry point, routes `/api/` to backend and `/` to Streamlit frontend. Uses `nginx:alpine`.
- **Backend API (Gunicorn):** Python 3.9 WSGI server running Flask and REST API endpoints.
- **Frontend (Streamlit):** Python 3.9 server rendering the UI.
- **Scheduler:** Isolated background worker using the backend image to handle cron jobs.
- **Database:** PostgreSQL 15 running in a container.

## 2. Existing Docker Services
- `nginx` (port 80)
- `backend` (internal port 5000)
- `scheduler` (internal background process)
- `frontend` (internal port 8501)
- `db` (internal port 5432)

## 3. Required Environment Variables
The following environment variables MUST be provided via `.env.production`:
- `FLASK_ENV=production`
- `SECRET_KEY` (Strong cryptographic random string)
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD` (Initial superadmin credentials)
- `DATABASE_URL` (e.g. `postgresql://shiptrack:<PASSWORD>@db:5432/shiptrack`)
- `POSTGRES_PASSWORD` (Must match the DB URL password)
- `TRACKING_PROVIDER` (Set to `india_post` for production)
- `TRACKING_DEMO_MODE=false`
- `OCR_ENGINE`
- `API_URL` (Usually `https://<DOMAIN>/api`)

## 4. Required Ports
- **Public:** `80` (HTTP), `443` (HTTPS)
- **Internal (Do not expose):** `5000` (Backend), `8501` (Frontend), `5432` (PostgreSQL)

## 5. Persistent Volumes
- `pgdata`: Holds PostgreSQL database state.
- `./uploads`: Host-mounted volume for persistent file uploads (OCR documents).

## 6. Database Requirements
- PostgreSQL 15.
- Must start completely empty (no SQLite, no demo seed data).
- Migrations must be run upon first deployment using `flask db upgrade`.

## 7. Scheduler Requirements
- Single dedicated container (`scheduler`) running `python backend/scheduler.py`.
- Must not be replicated alongside web workers to prevent concurrent duplicate jobs.

## 8. Reverse Proxy Requirements
- Nginx correctly handles `proxy_pass` to Gunicorn and Streamlit.
- WebSockets must be proxied properly for Streamlit (`Upgrade $http_upgrade`, `Connection "upgrade"`).
- Client body size increased for OCR document uploads (`client_max_body_size 16M`).

## 9. SSL Requirements
- Nginx must be configured to terminate SSL (port 443).
- Certificates must be generated (via Let's Encrypt / Certbot) once the VPS is active and DNS is pointing to the VPS IP.

## 10. Remaining Infrastructure Blockers
- **VPS Credentials:** Missing SSH access to the production Linux machine.
- **Domain Name:** Required for Let's Encrypt SSL issuance.
- **Firewall (UFW):** Must be configured to only allow 22, 80, and 443.
