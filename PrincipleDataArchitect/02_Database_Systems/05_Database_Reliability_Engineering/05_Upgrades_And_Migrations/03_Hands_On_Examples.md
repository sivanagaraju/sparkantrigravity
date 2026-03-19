# Hands-On Examples: Upgrades & Migrations

## 1. PostgreSQL Minor Version Upgrade

```bash
# Check current version
psql -c "SELECT version();"
# PostgreSQL 16.2 on x86_64-pc-linux-gnu

# Install the new minor version
sudo apt update
sudo apt install postgresql-16=16.3-1.pgdg22.04+1

# Restart PostgreSQL (only downtime: restart duration ~5 seconds)
sudo systemctl restart postgresql

# Verify
psql -c "SELECT version();"
# PostgreSQL 16.3 on x86_64-pc-linux-gnu
```

## 2. PostgreSQL Major Version Upgrade with pg_upgrade

### Pre-Upgrade Checklist
```bash
# 1. Install new version binaries (don't start the new cluster yet)
sudo apt install postgresql-17

# 2. Run pg_upgrade in check mode
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
  --old-datadir=/var/lib/postgresql/16/main \
  --new-datadir=/var/lib/postgresql/17/main \
  --old-bindir=/usr/lib/postgresql/16/bin \
  --new-bindir=/usr/lib/postgresql/17/bin \
  --check

# This reports:
# - Incompatible extensions
# - Data types removed in new version
# - Encoding mismatches
# - contrib module requirements
```

### Execute Upgrade (Link Mode)
```bash
# 3. Stop the old cluster
sudo systemctl stop postgresql@16-main

# 4. Run pg_upgrade with --link
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
  --old-datadir=/var/lib/postgresql/16/main \
  --new-datadir=/var/lib/postgresql/17/main \
  --old-bindir=/usr/lib/postgresql/16/bin \
  --new-bindir=/usr/lib/postgresql/17/bin \
  --link

# 5. Start the new cluster
sudo systemctl start postgresql@17-main

# 6. Run the generated analyze script (updates statistics)
sudo -u postgres /var/lib/postgresql/17/main/analyze_new_cluster.sh

# 7. After verifying everything works, delete old cluster
sudo -u postgres /var/lib/postgresql/17/main/delete_old_cluster.sh
```

## 3. Zero-Downtime Upgrade via Logical Replication

### Setup (PG 15 → PG 16)
```sql
-- On PG 15 (source): configure wal_level
ALTER SYSTEM SET wal_level = 'logical';
-- Restart PG 15 for wal_level to take effect

-- On PG 15: create publication
CREATE PUBLICATION upgrade_pub FOR ALL TABLES;

-- On PG 16 (target): Create schema (no data)
-- Run: pg_dump --schema-only -h pg15-host mydb | psql -h pg16-host mydb

-- On PG 16: create subscription
CREATE SUBSCRIPTION upgrade_sub
  CONNECTION 'host=pg15-host port=5432 dbname=mydb user=repl_user'
  PUBLICATION upgrade_pub;

-- Monitor sync progress
SELECT * FROM pg_stat_subscription;
-- Wait until srsubstate = 'r' (ready) for all tables
```

### Switchover
```sql
-- 1. Set PG 15 to read-only (prevent new writes)
-- On PG 15:
ALTER SYSTEM SET default_transaction_read_only = on;
SELECT pg_reload_conf();

-- 2. Wait for PG 16 to catch up (check replication lag = 0)
-- On PG 16:
SELECT pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn();

-- 3. Fix sequences on PG 16 (logical replication doesn't sync sequences)
-- For each sequence, set it to at least the current value on PG 15:
SELECT setval('orders_id_seq', (SELECT last_value FROM dblink(
  'host=pg15-host dbname=mydb', 'SELECT last_value FROM orders_id_seq'
) AS t(last_value bigint)));

-- 4. Drop subscription on PG 16 (clean up)
DROP SUBSCRIPTION upgrade_sub;

-- 5. Point application to PG 16 (update connection string / DNS)
```

## 4. Safe Schema Migration with Lock Timeout

```sql
-- Always set lock_timeout before DDL
BEGIN;
SET lock_timeout = '5s';

-- Add a nullable column (instant, metadata-only in PG 11+)
ALTER TABLE orders ADD COLUMN priority integer;

-- Create index concurrently (must be outside a transaction)
COMMIT;
CREATE INDEX CONCURRENTLY idx_orders_priority ON orders(priority);

-- Add NOT NULL constraint with validation
-- Step 1: Add constraint as NOT VALID (instant, no table scan)
ALTER TABLE orders ADD CONSTRAINT orders_priority_nn
  CHECK (priority IS NOT NULL) NOT VALID;

-- Step 2: Validate in background (scans table but doesn't block writes)
ALTER TABLE orders VALIDATE CONSTRAINT orders_priority_nn;
```

## 5. Flyway Migration Example

### Directory Structure
```
db/migration/
├── V1__create_users_table.sql
├── V2__add_email_to_users.sql
├── V3__create_orders_table.sql
├── V4__add_index_on_orders_created_at.sql
└── V5__add_priority_to_orders.sql
```

### V5__add_priority_to_orders.sql
```sql
-- Safe: nullable column with no default (instant in PG 11+)
ALTER TABLE orders ADD COLUMN priority integer;

-- Safe: concurrent index (Flyway must not wrap this in a transaction)
-- Add to flyway.conf: flyway.mixed=true
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_priority 
  ON orders(priority);
```

### `flyway.conf`
```properties
flyway.url=jdbc:postgresql://localhost:5432/mydb
flyway.user=flyway_user
flyway.password=${FLYWAY_PASSWORD}
flyway.schemas=public
flyway.mixed=true              # Allow mixing transactional and non-transactional statements
flyway.outOfOrder=false        # Enforce strict ordering
flyway.baselineOnMigrate=true  # Baseline for existing databases
```

### Run Migration
```bash
flyway -configFiles=flyway.conf migrate

# Output:
# Successfully applied 1 migration (V5__add_priority_to_orders.sql)
# Schema version: 5
```
