# Hands-On Examples: Connection Pooling

## 1. PgBouncer Configuration

### `pgbouncer.ini` — Production Configuration
```ini
[databases]
# Map virtual database names to actual PostgreSQL servers
myapp = host=pg-primary.internal port=5432 dbname=production

[pgbouncer]
# Listen on all interfaces, port 6432
listen_addr = 0.0.0.0
listen_port = 6432

# CRITICAL: Transaction mode for maximum pooling benefit
pool_mode = transaction

# Pool sizing
default_pool_size = 20          # Connections per database/user pair
min_pool_size = 5               # Keep warm connections ready
reserve_pool_size = 5           # Extra connections for burst traffic
reserve_pool_timeout = 3        # Wait 3s before dipping into reserve

# Client limits
max_client_conn = 1000          # Accept up to 1000 app connections
max_db_connections = 25         # Never open more than 25 to PostgreSQL

# Connection lifecycle
server_lifetime = 3600          # Recycle server connections every hour
server_idle_timeout = 600       # Close idle server connections after 10 min
server_connect_timeout = 5      # Fail if Postgres doesn't respond in 5s
query_timeout = 300             # Kill queries running > 5 minutes

# Authentication
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Logging
log_connections = 0             # Don't log every connect (too noisy)
log_disconnections = 0
stats_period = 60               # Emit stats every 60 seconds
```

### `userlist.txt`
```
"myapp_user" "SCRAM-SHA-256$4096:salt$stored_key:server_key"
```

### Monitor PgBouncer
```sql
-- Connect to PgBouncer's admin console
psql -h localhost -p 6432 -U pgbouncer pgbouncer

-- Show active pools
SHOW POOLS;
-- database | user | cl_active | cl_waiting | sv_active | sv_idle | sv_used | pool_mode
-- myapp    | myapp_user | 45  | 0          | 12        | 8       | 5       | transaction

-- Show connection stats
SHOW STATS;

-- Show client connections
SHOW CLIENTS;

-- Show server connections  
SHOW SERVERS;
```

## 2. HikariCP Configuration (Spring Boot)

### `application.yml`
```yaml
spring:
  datasource:
    url: jdbc:postgresql://pgbouncer-host:6432/myapp
    username: myapp_user
    password: ${DB_PASSWORD}
    hikari:
      # Pool size: small because PgBouncer handles multiplexing
      maximum-pool-size: 5
      minimum-idle: 5           # Fixed-size pool (recommended by HikariCP)
      
      # Timeouts
      connection-timeout: 3000  # 3 seconds — fail fast, don't block the request
      idle-timeout: 600000      # 10 minutes
      max-lifetime: 1800000     # 30 minutes (< PgBouncer server_lifetime)
      
      # Validation
      connection-test-query: SELECT 1
      validation-timeout: 2000
      
      # Leak detection — logs a stack trace if a connection isn't returned
      leak-detection-threshold: 30000  # 30 seconds
      
      # Pool name for JMX monitoring
      pool-name: myapp-hikari-pool
```

## 3. ProxySQL Configuration for MySQL Read/Write Split

```sql
-- Connect to ProxySQL admin interface
mysql -h 127.0.0.1 -P 6032 -u admin -p

-- Define backend servers in hostgroups
-- Hostgroup 0 = writes (primary), Hostgroup 1 = reads (replicas)
INSERT INTO mysql_servers (hostgroup_id, hostname, port, max_connections)
VALUES 
  (0, 'mysql-primary.internal', 3306, 50),
  (1, 'mysql-replica-1.internal', 3306, 100),
  (1, 'mysql-replica-2.internal', 3306, 100);

-- Query routing rules
INSERT INTO mysql_query_rules (rule_id, match_pattern, destination_hostgroup, apply)
VALUES 
  (1, '^SELECT .* FOR UPDATE', 0, 1),   -- SELECT FOR UPDATE → primary
  (2, '^SELECT', 1, 1),                  -- Regular SELECT → replicas
  (3, '.*', 0, 1);                       -- Everything else → primary

-- Apply changes
LOAD MYSQL SERVERS TO RUNTIME;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
SAVE MYSQL QUERY RULES TO DISK;
```

## 4. Python Connection Pooling with SQLAlchemy

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://user:pass@pgbouncer:6432/myapp",
    
    # Pool configuration
    pool_size=5,              # 5 persistent connections
    max_overflow=3,           # Allow 3 extra connections during bursts
    pool_timeout=5,           # Wait max 5s for a connection
    pool_recycle=1800,        # Recycle connections every 30 min
    pool_pre_ping=True,       # Validate connection health before use
    
    # Echo SQL for debugging (disable in production)
    echo=False,
)

# Usage with context manager (ensures connection return)
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM orders WHERE id = :id"), {"id": 42})
    order = result.fetchone()
# Connection automatically returned to pool here
```
