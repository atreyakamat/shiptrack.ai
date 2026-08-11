# ShipTrack AI - Backup & Restore Procedures

## 1. How to Create a Backup
To create a production database backup without stopping the application, run the following command on the VPS. This extracts a SQL dump from the running PostgreSQL container.

```bash
docker exec -t shiptrack-db-1 pg_dump -U shiptrack -d shiptrack -F c -f /tmp/db_backup.dump
docker cp shiptrack-db-1:/tmp/db_backup.dump ./backups/db_backup_$(date +%Y%m%d_%H%M%S).dump
```

**Uploads Backup (OCR files):**
```bash
tar -czvf ./backups/uploads_backup_$(date +%Y%m%d).tar.gz ./uploads
```

## 2. Where Backup is Stored
By default, the commands above store the backups in the `./backups` directory on the host VPS. **IMPORTANT:** These files must be copied off-site (e.g., AWS S3, local machine, another VPS) to ensure disaster recovery.

## 3. How to Restore
If data is corrupted and you need to restore from a backup:

1. Stop the application services (keep the DB running):
```bash
docker compose stop backend frontend scheduler
```
2. Drop and recreate the database schema to ensure a clean slate:
```bash
docker exec -it shiptrack-db-1 dropdb -U shiptrack shiptrack
docker exec -it shiptrack-db-1 createdb -U shiptrack shiptrack
```
3. Copy the backup file into the container and restore:
```bash
docker cp ./backups/db_backup_20260811_120000.dump shiptrack-db-1:/tmp/db_backup.dump
docker exec -t shiptrack-db-1 pg_restore -U shiptrack -d shiptrack -1 /tmp/db_backup.dump
```
4. Restart all services:
```bash
docker compose up -d
```

## 4. How to Verify Backup
To verify a backup, NEVER restore it into the live production database.
Instead, spin up a temporary, isolated PostgreSQL container:
```bash
docker run --name pg-verify -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=shiptrack -d postgres:15-alpine
docker cp ./backups/db_backup.dump pg-verify:/tmp/
docker exec -it pg-verify pg_restore -U test -d shiptrack -1 /tmp/db_backup.dump
docker exec -it pg-verify psql -U test -d shiptrack -c "SELECT COUNT(*) FROM shipment;"
docker rm -f pg-verify
```

## 5. Recommended Backup Frequency
- **Database:** Daily (Automated via a cron job on the host VPS).
- **Uploads:** Weekly (or daily depending on volume).

## 6. What Happens if the VPS is Destroyed?
If the entire VPS is destroyed, you will need:
1. The `.env` and `.env.production` files (Keep these backed up securely in a password manager!).
2. The latest `db_backup.dump`.
3. The latest `uploads_backup.tar.gz`.
Deploy a new VPS, clone the repository, restore the uploads folder, start `docker compose up -d db`, perform the database restore (Step 3), and then `docker compose up -d` to bring the application back online.
