#!/usr/bin/env bash
# ==============================================================================
# SmartSched AI — Automated PostgreSQL Database Backup Script
# Usage: ./backend/scripts/backup_postgres.sh
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./data/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/smartsched_pg_backup_${TIMESTAMP}.sql.gz"
DB_NAME="${PGDATABASE:-smartsched}"
PG_HOST="${PGHOST:-localhost}"
PG_PORT="${PGPORT:-5432}"
PG_USER="${PGUSER:-sagarsukhadev}"

mkdir -p "${BACKUP_DIR}"

echo "Starting automated PostgreSQL backup for database '${DB_NAME}'..."
/opt/homebrew/Cellar/postgresql@16/16.16/bin/pg_dump -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

echo "Backup completed successfully: ${BACKUP_FILE} ($(ls -lh "${BACKUP_FILE}" | awk '{print $5}'))"

# Retention policy: Keep backups for 30 days
find "${BACKUP_DIR}" -name "smartsched_pg_backup_*.sql.gz" -mtime +30 -exec rm -f {} \; 2>/dev/null || true
echo "Retention policy verified (older than 30 days purged)."
