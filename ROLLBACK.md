# ShipTrack AI - Rollback Procedure

## Overview
A rollback is required when a new deployment introduces critical bugs that cannot be fixed immediately. The goal of this rollback is to revert the application code (Docker images) back to the last known-good state.

## 1. Prerequisites
- The exact git commit SHA of the previous known-good deployment.
- Database backup taken *before* the failed deployment (if database migrations were applied).

## 2. Reverting Application Code
To revert the application code without altering the database:

1. View the git deployment history to find the previous commit:
```bash
cat DEPLOYMENT_VERSION
git log --oneline -5
```
2. Checkout the known-good commit:
```bash
git fetch
git checkout <KNOWN_GOOD_COMMIT_SHA>
```
3. Rebuild and restart the Docker containers:
```bash
docker compose build
docker compose up -d
```
4. Verify the application is healthy.

## 3. Reverting Database Schema (If Migrations Failed)
> [!WARNING]
> Database rollbacks are destructive. Only perform a database rollback if the new code introduced backward-incompatible schema changes that break the old application code.

If you must rollback the database to match the old code:

1. Stop the application services (so no new data is written):
```bash
docker compose stop backend frontend scheduler
```
2. (Optional, if you know the exact migration downgrade):
```bash
docker compose run --rm backend flask db downgrade <TARGET_REVISION>
```
3. (Alternative: Restore from pre-deployment backup):
If the schema is corrupted or `downgrade` fails, drop the database and restore the `db_backup.dump` taken immediately prior to the deployment (See `BACKUP_RESTORE.md`).

4. Once the database matches the old schema, start the services:
```bash
docker compose up -d
```

## 4. Post-Rollback Verification
1. Ensure the Nginx reverse proxy is correctly serving the app.
2. Login to the application to verify session and database connectivity.
3. Check backend logs for persistent errors:
```bash
docker compose logs -f backend
```
