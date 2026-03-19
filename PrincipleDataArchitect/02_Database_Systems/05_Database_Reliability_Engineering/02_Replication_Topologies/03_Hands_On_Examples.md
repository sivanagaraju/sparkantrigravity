# Hands-On Examples: Replication Topologies

## 1. Setting Up PostgreSQL Streaming Replication

### Primary Configuration (`postgresql.conf`)
```ini
# Enable WAL level sufficient for replication
wal_level = replica

# Allow up to 5 replication connections
max_wal_senders = 5

# Keep at least 1 GB of WAL for slow replicas
wal_keep_size = '1GB'

# Enable replication slots (prevent WAL recycling before replica consumes)
max_replication_slots = 5
```

### Primary: Create Replication User and Slot
```sql
-- Create a dedicated replication user (least privilege)
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'strong_password';

-- Create a physical replication slot (prevents WAL recycling)
SELECT pg_create_physical_replication_slot('replica_slot_1');

-- Verify slot exists
SELECT slot_name, active, restart_lsn FROM pg_replication_slots;
```

### Primary: Allow Replication in `pg_hba.conf`
```
# TYPE   DATABASE   USER          ADDRESS          METHOD
host     replication replicator   10.0.0.0/24      scram-sha-256
```

### Standby: Take Base Backup and Start
```bash
# Take a base backup from the primary
pg_basebackup -h primary-host -U replicator -D /var/lib/postgresql/16/standby \
  -Fp -Xs -P -R --slot=replica_slot_1

# The -R flag auto-creates standby.signal and configures primary_conninfo
# Verify the auto-generated postgresql.auto.conf:
cat /var/lib/postgresql/16/standby/postgresql.auto.conf
# primary_conninfo = 'host=primary-host user=replicator password=strong_password'
# primary_slot_name = 'replica_slot_1'

# Start the standby
pg_ctl -D /var/lib/postgresql/16/standby start
```

### Monitor Replication Health
```sql
-- On the PRIMARY: check connected replicas
SELECT 
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS send_lag_bytes,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replay_lag_bytes,
    reply_time
FROM pg_stat_replication;

-- On the STANDBY: check replication status
SELECT 
    pg_is_in_recovery() AS is_standby,
    pg_last_wal_receive_lsn() AS received_lsn,
    pg_last_wal_replay_lsn() AS replayed_lsn,
    pg_last_xact_replay_timestamp() AS last_replayed_at,
    now() - pg_last_xact_replay_timestamp() AS replay_delay;
```

## 2. Configuring Synchronous Replication

```sql
-- On the primary: designate sync standbys
ALTER SYSTEM SET synchronous_standby_names = 'FIRST 1 (standby1, standby2)';
-- Meaning: wait for the FIRST 1 standby in the list to confirm

-- For quorum-based: wait for ANY 2 of 3 standbys
ALTER SYSTEM SET synchronous_standby_names = 'ANY 2 (standby1, standby2, standby3)';

SELECT pg_reload_conf();

-- Verify sync state
SELECT application_name, sync_state FROM pg_stat_replication;
-- sync_state: 'sync' (designated synchronous), 'async', 'potential', 'quorum'
```

## 3. Setting Up Logical Replication

### Publisher (Source Database)
```sql
-- Ensure wal_level is 'logical'
ALTER SYSTEM SET wal_level = 'logical';
-- Requires restart

-- Create a publication for specific tables
CREATE PUBLICATION pub_orders FOR TABLE orders, order_items;

-- Or publish ALL tables
CREATE PUBLICATION pub_all FOR ALL TABLES;
```

### Subscriber (Target Database)
```sql
-- Create the same table structure (DDL is NOT replicated)
CREATE TABLE orders (id serial PRIMARY KEY, customer_id int, total numeric);
CREATE TABLE order_items (id serial PRIMARY KEY, order_id int, product text);

-- Create the subscription
CREATE SUBSCRIPTION sub_orders
    CONNECTION 'host=primary-host dbname=mydb user=replicator password=pass'
    PUBLICATION pub_orders;

-- Monitor subscription status
SELECT * FROM pg_stat_subscription;
```

## 4. Manual Failover (PostgreSQL)

```bash
# On the standby: promote to primary
pg_ctl -D /var/lib/postgresql/16/standby promote

# Or use SQL (PostgreSQL 12+):
# SELECT pg_promote();

# Verify: the standby.signal file is removed
ls /var/lib/postgresql/16/standby/standby.signal
# File not found — promotion successful

# The old primary must NOT be restarted as-is
# It must be rebuilt as a new standby using pg_rewind or pg_basebackup
```

## 5. Automated Failover with Patroni

```yaml
# patroni.yml (simplified)
scope: prod-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008

etcd:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576  # 1 MB max lag for failover
    synchronous_mode: true
  postgresql:
    parameters:
      max_connections: 200
      wal_level: replica

postgresql:
  listen: 0.0.0.0:5432
  data_dir: /var/lib/postgresql/16/data
  authentication:
    replication:
      username: replicator
      password: secret
```
