# Hands-On Examples: Backup & Recovery Strategies

## 1. Logical Backup with pg_dump

### Full Database Dump (Custom Format)
```bash
# Custom format: compressed, supports parallel restore
pg_dump -h localhost -U postgres -Fc -j 4 -f /backups/mydb_$(date +%Y%m%d_%H%M%S).dump mydb

# Flags:
# -Fc : Custom format (compressed, most flexible)
# -j 4 : 4 parallel workers (requires -Fd for directory format)
# -f   : Output file
```

### Schema-Only Dump (for migration planning)
```bash
pg_dump -h localhost -U postgres --schema-only -f schema.sql mydb
```

### Single Table Dump
```bash
pg_dump -h localhost -U postgres -Fc -t orders -f orders_backup.dump mydb
```

### Parallel Restore
```bash
pg_restore -h localhost -U postgres -d mydb_restored -j 8 \
  --no-owner --no-privileges --clean --if-exists \
  /backups/mydb_20240315_143000.dump

# --clean --if-exists : Drop objects before recreating (idempotent restore)
# -j 8 : 8 parallel workers for data load + index creation
```

## 2. Physical Backup with pg_basebackup

### Basic Base Backup
```bash
pg_basebackup -h pg-primary -U replication_user \
  -D /backups/base_$(date +%Y%m%d) \
  -Ft -z -P --wal-method=stream

# -Ft : Tar format
# -z  : gzip compression
# -P  : Show progress
# --wal-method=stream : Stream WAL during backup (ensures self-contained backup)
```

### Restore from Base Backup
```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Clear the data directory
rm -rf /var/lib/postgresql/16/main/*

# Extract the base backup
tar xzf /backups/base_20240315/base.tar.gz -C /var/lib/postgresql/16/main/
tar xzf /backups/base_20240315/pg_wal.tar.gz -C /var/lib/postgresql/16/main/pg_wal/

# Start PostgreSQL (it will replay WAL from the backup and enter normal operation)
sudo systemctl start postgresql
```

## 3. PITR with pgBackRest

### Initial Setup
```bash
# /etc/pgbackrest.conf
[global]
repo1-path=/var/lib/pgbackrest
repo1-retention-full=2
repo1-retention-diff=7
repo1-cipher-pass=<encryption-passphrase>
repo1-cipher-type=aes-256-cbc
compress-type=zstd
compress-level=3

# S3 remote repository
repo2-type=s3
repo2-s3-bucket=mydb-backups
repo2-s3-region=us-east-1
repo2-s3-endpoint=s3.amazonaws.com
repo2-path=/pgbackrest
repo2-retention-full=4
repo2-retention-diff=14

[main]
pg1-path=/var/lib/postgresql/16/main
pg1-port=5432
```

### PostgreSQL Configuration for pgBackRest
```ini
# postgresql.conf
archive_mode = on
archive_command = 'pgbackrest --stanza=main archive-push %p'
archive_timeout = 60
```

### Create Stanza and First Full Backup
```bash
# Initialize the stanza (metadata about this PostgreSQL cluster)
pgbackrest --stanza=main stanza-create

# Verify configuration
pgbackrest --stanza=main check

# Full backup
pgbackrest --stanza=main --type=full backup

# Differential backup (daily)
pgbackrest --stanza=main --type=diff backup

# Incremental backup (hourly)
pgbackrest --stanza=main --type=incr backup
```

### Point-in-Time Recovery
**Scenario:** Someone ran `DELETE FROM orders WHERE 1=1` at 2024-03-15 14:35:00 UTC. You need to recover to 14:34:59.

```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Restore to the target time
pgbackrest --stanza=main --type=time \
  "--target=2024-03-15 14:34:59.000000+00" \
  --target-action=promote \
  --delta restore

# --delta : Only restore files that differ (fast for large databases)
# --target-action=promote : Automatically promote to read-write after recovery

# Start PostgreSQL
sudo systemctl start postgresql
```

### Verify Backup Integrity
```bash
# Verify all backups in the repository
pgbackrest --stanza=main verify

# List backups with details
pgbackrest --stanza=main info
```

## 4. Automated Backup Script with Monitoring

```bash
#!/bin/bash
# /usr/local/bin/pgbackup.sh
set -euo pipefail

STANZA="main"
BACKUP_TYPE="${1:-incr}"  # full, diff, or incr
ALERT_WEBHOOK="https://hooks.slack.com/services/xxx"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

send_alert() {
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H 'Content-type: application/json' \
        -d "{\"text\": \"🚨 Backup FAILED: $1\"}" || true
}

log "Starting $BACKUP_TYPE backup for stanza $STANZA"

if ! pgbackrest --stanza="$STANZA" --type="$BACKUP_TYPE" backup 2>&1; then
    send_alert "pgBackRest $BACKUP_TYPE backup failed on $(hostname)"
    exit 1
fi

log "Backup completed. Running verification..."

if ! pgbackrest --stanza="$STANZA" verify 2>&1; then
    send_alert "pgBackRest verify failed after $BACKUP_TYPE backup on $(hostname)"
    exit 1
fi

log "Verification passed. Backup successful."
```

### Cron Schedule
```cron
# Full backup: Sunday 2 AM
0 2 * * 0 /usr/local/bin/pgbackup.sh full >> /var/log/pgbackup.log 2>&1

# Differential: Daily 2 AM (except Sunday)
0 2 * * 1-6 /usr/local/bin/pgbackup.sh diff >> /var/log/pgbackup.log 2>&1

# Incremental: Every 4 hours
0 */4 * * * /usr/local/bin/pgbackup.sh incr >> /var/log/pgbackup.log 2>&1
```

## 5. MySQL Backup with Percona XtraBackup

```bash
# Full backup (hot, non-blocking for InnoDB)
xtrabackup --backup --target-dir=/backups/full_$(date +%Y%m%d)

# Incremental backup
xtrabackup --backup --target-dir=/backups/incr_$(date +%Y%m%d_%H) \
  --incremental-basedir=/backups/full_20240315

# Prepare for restore (apply redo log)
xtrabackup --prepare --target-dir=/backups/full_20240315

# Restore
sudo systemctl stop mysql
xtrabackup --copy-back --target-dir=/backups/full_20240315
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysql
```
