# ShipTrack AI - Rollback Procedure

**Version:** RC2  
**Environment:** Production (Docker Compose)  
**Last Updated:** 2025-08-11

---

## 🎯 Overview

Rollback reverts the **application code (Docker images)** to a previous known-good commit. Database rollbacks are separate and more dangerous - see Section 3.

### When to Rollback
- Critical bug in new deployment (5xx errors, data corruption, security issue)
- Performance regression causing timeouts
- Migration failure leaving DB in broken state

### Rollback Principles
1. **Code first, DB last** - Revert Docker images before touching database
2. **Preserve data** - Never drop database unless absolutely necessary
3. **Test first** - Verify rollback target commit works in staging if possible
4. **Document** - Record what was rolled back and why

---

## 1. PREREQUISITES

### Required Information
| Item | Source |
|------|--------|
| Current deployment commit | `cat DEPLOYMENT_VERSION` |
| Previous known-good commit | `git log --oneline -10` |
| Database backup before failed deploy | `/opt/shiptrack-ai/backups/db_backup_*.dump` |
| Migration status | `docker compose run --rm backend flask db current` |

### Pre-Rollback Checklist
- [ ] Identify target commit SHA (known-good)
- [ ] Verify database backup exists from before failed deployment
- [ ] Alert team/stakeholders of rollback
- [ ] Ensure no active writes (maintenance window if possible)

---

## 2. CODE ROLLBACK (Application Only - No DB Changes)

### Standard Rollback Procedure

```bash
cd /opt/shiptrack-ai

# 1. Record current (bad) commit for reference
CURRENT_COMMIT=$(cat DEPLOYMENT_VERSION)
echo "Current (bad) commit: ${CURRENT_COMMIT}"

# 2. View recent commits to identify target
git log --oneline -10
# Example output:
# a1b2c3d (HEAD -> main) BAD: Breaking change in shipment detail
# 9f8e7d6 GOOD: RC2 stabilization
# 5d4c3b2 feat: add analytics

# 3. Checkout known-good commit
TARGET_COMMIT="9f8e7d6"  # Replace with actual SHA
git checkout ${TARGET_COMMIT}

# 4. Update deployment version marker
git rev-parse HEAD > DEPLOYMENT_VERSION
echo "Rolled back to: $(cat DEPLOYMENT_VERSION)"

# 5. Rebuild and restart containers
docker compose build
docker compose up -d

# 6. Verify health
sleep 15
curl -f http://localhost/api/health
echo "Code rollback complete. Verify application functionality."
```

### Rollback to Specific Tag (If Tagged)

```bash
# List tags
git tag -l "v1.0.0*"

# Checkout tag
git checkout v1.0.0-rc2

# Update version marker
git rev-parse HEAD > DEPLOYMENT_VERSION

# Rebuild and deploy
docker compose build
docker compose up -d
```

---

## 3. DATABASE ROLLBACK (⚠️ HIGH RISK)

### When Database Rollback Is Needed
- Migration applied that is **backward-incompatible** with old code
- Migration failed halfway, leaving DB in inconsistent state
- Data corruption from application bug

### ⚠️ WARNING
- Database rollbacks are **destructive** - data written after backup is LOST
- Only rollback DB if old code **cannot work** with new schema
- Prefer: Fix forward with new migration instead of rolling back

### Option A: Alembic Downgrade (If Migration Is Reversible)

```bash
cd /opt/shiptrack-ai

# 1. Stop app services (prevent writes during downgrade)
docker compose stop backend frontend scheduler nginx

# 2. Check current revision
docker compose run --rm backend flask db current

# 3. Check target revision (one before bad migration)
docker compose run --rm backend flask db history

# 4. Downgrade to target revision
# Replace <TARGET_REVISION> with actual revision ID (e.g., "abc123")
docker compose run --rm backend flask db downgrade <TARGET_REVISION>

# 5. Verify
docker compose run --rm backend flask db current

# 6. Restart services
docker compose up -d
```

### Option B: Restore from Pre-Deployment Backup (If Downgrade Fails)

```bash
cd /opt/shiptrack-ai

BACKUP_FILE="backups/db_backup_20250811_023000.dump"  # From BEFORE failed deploy

# 1. Stop app services
docker compose stop backend frontend scheduler nginx

# 2. Drop and recreate database
docker exec -it shiptrack-ai-db-1 dropdb -U shiptrack shiptrack || true
docker exec -it shiptrack-ai-db-1 createdb -U shiptrack shiptrack

# 3. Restore backup
docker cp "${BACKUP_FILE}" shiptrack-ai-db-1:/tmp/db_backup.dump
docker exec -t shiptrack-ai-db-1 pg_restore -U shiptrack -d shiptrack -1 /tmp/db_backup.dump
docker exec shiptrack-ai-db-1 rm /tmp/db_backup.dump

# 4. Verify schema matches rolled-back code
docker compose run --rm backend flask db current

# 5. Restart all services
docker compose up -d
```

---

## 4. POST-ROLLBACK VERIFICATION

### Immediate Checks (Within 5 minutes)

```bash
# 1. All containers running
docker compose ps
# All should show "Up" with (healthy) for db

# 2. API health
curl -f http://localhost/api/health
# {"status":"ok","version":"1.0.0",...}

# 3. Frontend loads
curl -f http://localhost/ | grep -i "shiptrack" || echo "Frontend check failed"

# 4. Backend logs clean
docker compose logs --tail=20 backend | grep -iE "(error|exception|traceback)" || echo "No errors in recent logs"

# 5. Scheduler running
docker compose logs --tail=10 scheduler | grep -i "scheduler" || echo "Scheduler check needed"
```

### Functional Verification (Within 30 minutes)

| Test | Command/Action | Expected |
|------|----------------|----------|
| Login | Open https://domain, login with admin | Success, dashboard loads |
| Shipments List | Navigate to Shipments page | List renders |
| Shipment Detail | Click any shipment | Detail page renders, **no raw HTML**, no "None" values |
| Timeline | Check timeline on detail | Dates/times correct, no blank fields |
| Progress Bar | Check progress on detail | Correct stage highlighted |
| OCR Upload | Upload test receipt | Processes or shows demo notice |
| AI Insights | Click "Explain Current Status" | Generates summary or "No AI insight" |
| Analytics | Navigate to Analytics | Charts render |
| CSV Export | Click Export CSV | Downloads file |

### Data Integrity Checks

```bash
# Verify record counts haven't unexpectedly dropped
docker compose exec db psql -U shiptrack -d shiptrack -c "
SELECT 'users' as table, COUNT(*) FROM \"user\"
UNION ALL SELECT 'shipments', COUNT(*) FROM shipment
UNION ALL SELECT 'tracking_events', COUNT(*) FROM tracking_event
UNION ALL SELECT 'ai_summaries', COUNT(*) FROM ai_summary;
"
```

---

## 5. ROLLBACK DECISION TREE

```
┌─────────────────────────────────────┐
│  Deployment Failed / Bug Reported   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Is it a CODE bug (logic, UI, API)? │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
     YES              NO
       │               │
       ▼               ▼
┌──────────────┐  ┌────────────────────────────┐
│ CODE ROLLBACK │  │ Is it a MIGRATION issue?   │
│ (Section 2)   │  └──────────────┬─────────────┘
└──────────────┘                 │
               ┌─────────────────┴─────────────────┐
               ▼                                   ▼
            YES                                   NO
               │                                   │
               ▼                                   ▼
    ┌─────────────────────┐              ┌─────────────────┐
    │ Try Alembic         │              │ Investigate:    │
    │ Downgrade           │              │ - Data bug?     │
    │ (Section 3A)        │              │ - Config issue? │
    └──────────┬──────────┘              └─────────────────┘
               │
          ┌────┴────┐
          ▼         ▼
        WORKS   FAILS
          │         │
          ▼         ▼
    Verify &     Restore from
    Deploy       Pre-deploy Backup
                 (Section 3B)
```

---

## 6. COMMUNICATION TEMPLATE

### Rollback Initiation (Slack/Email)
```
🔴 ROLLBACK INITIATED - ShipTrack AI Production

**Time:** 2025-08-11 14:30 UTC
**Initiated by:** [Name]
**Current Commit:** a1b2c3d (BAD)
**Target Commit:** 9f8e7d6 (GOOD - RC2)
**Reason:** [Brief: "Shipment detail page shows raw HTML / 500 errors on analytics"]

**Impact:** Brief downtime (~2-3 min during container restart)
**DB Rollback:** [No / Yes - Alembic / Yes - Full Restore]

**Verification Plan:** 
- [ ] API health returns 200
- [ ] Login works
- [ ] Shipment detail renders correctly
- [ ] No raw HTML / None values

**ETA:** 15 minutes
```

### Rollback Complete
```
✅ ROLLBACK COMPLETE - ShipTrack AI Production

**Time:** 2025-08-11 14:45 UTC
**Rolled Back To:** 9f8e7d6 (RC2 Stabilization)
**DB Rollback:** No
**Verification:** All checks passed
- API health: OK
- Login: OK
- Shipment detail: OK (no raw HTML, correct timestamps)
- Timeline: OK
- Progress bar: OK
- OCR: OK
- AI: OK

**Next Steps:**
- Create hotfix branch from 9f8e7d6
- Root cause analysis scheduled
- Hotfix deployment planned for [date]
```

---

## 7. ROLLBACK LOG TEMPLATE

Record every rollback in `/opt/shiptrack-ai/rollbacks.log`:

```markdown
## 2025-08-11 14:30 UTC - Rollback #1

**Trigger:** Shipment detail page rendering raw HTML after commit a1b2c3d
**Type:** Code rollback only
**From Commit:** a1b2c3d (HEAD)
**To Commit:** 9f8e7d6 (RC2 Stabilization)
**DB Rollback:** None
**Duration:** 3 minutes
**Verified By:** [Name]
**Status:** ✅ Success

**Root Cause:** Missing `textwrap.dedent()` in timeline.py HTML generation
**Fix Applied:** Hotfix commit f1e2d3c on branch hotfix/timeline-html
**Re-deployment:** Planned 2025-08-12
```

---

## 8. QUICK REFERENCE CARD

| Scenario | Command | Time |
|----------|---------|------|
| **Code rollback (standard)** | `git checkout <GOOD_SHA> && docker compose build && docker compose up -d` | ~2 min |
| **Code rollback (tag)** | `git checkout v1.0.0-rc2 && docker compose build && docker compose up -d` | ~2 min |
| **DB downgrade (alembic)** | `docker compose stop backend frontend scheduler nginx && docker compose run --rm backend flask db downgrade <REV>` | ~1 min |
| **DB full restore** | `docker compose stop backend frontend scheduler nginx && [drop/create/restore] && docker compose up -d` | ~5 min |
| **Verify health** | `curl -f http://localhost/api/health` | <1 sec |
| **Check logs** | `docker compose logs --tail=50 backend` | <1 sec |

---

*Keep this document with the deployment. Update after every rollback.*