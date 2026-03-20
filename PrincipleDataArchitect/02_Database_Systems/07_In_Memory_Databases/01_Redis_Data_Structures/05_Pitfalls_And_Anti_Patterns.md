# Pitfalls and Anti-Patterns: Redis Data Structures

## M01: The Big Key (O(N) Deletion Spike)

### The Mistake
Storing millions of elements in a single Hash, Set, or ZSet. Redis has a 512MB limit per string, but a Hash can theoretically hold 2^32 fields.
When a developer deletes this key (e.g., `DEL huge_hash`), Redis must traverse and free the memory for all 10 million fields synchronously.

### The Impact
Deleting a Hash with 10 million fields takes **~5 to 10 seconds**. Because Redis executes commands on a single thread, **all other operations are blocked** for those 5 seconds. P99 latency goes to 5000ms. End-users see gateway timeouts.

### Detection
Use the Redis CLI to find large keys asynchronously (won't block execution):
```bash
# Good: Samples keys and reports the largest ones it finds
redis-cli --bigkeys

# Debugging specific command latency
redis-cli --latency-history
```

### The Fix
Never use `DEL` on large collections. Use **`UNLINK`** (introduced in Redis 4.0), which unlinks the key from the dictionary in O(1) time and pushes the memory reclamation to a background thread.
```bash
❌ DEL huge_hash
✅ UNLINK huge_hash
```

---

## M02: Massive Pipelining Causing OOM (Output Buffer Swell)

### The Mistake
Using pipelines to send 1,000,000 commands to Redis at once to "speed up bulk loading."

### The Impact
Pipelining saves network round trips, but Redis must execute all 1,000,000 commands and **buffer all 1,000,000 responses** in memory before flushing them back to the client. This massive `client-output-buffer` can consume GBs of RAM and trigger Out Of Memory (OOM) killer or force Redis to evict unrelated cache keys.

### Detection
Monitor the `client_longest_output_list` and `client_biggest_input_buf` metrics in the `INFO clients` command.
```bash
redis-cli INFO clients
```

### The Fix
Batch pipelines into chunks of **1,000 to 10,000** commands. This guarantees high throughput without destroying the memory heap.

---

## M03: Keyspace Scanning in Production

### The Mistake
Using `KEYS *` or `KEYS user_*` to find elements or clean up the database.

### The Impact
`KEYS` performs an O(N) linear scan over the entire dictionary. A database with 50 million keys will lock the main thread for **~10 seconds**.

### Detection
Check the `SLOWLOG` for `KEYS` commands.
```bash
SLOWLOG GET 10
```

### The Fix
Use `SCAN`, `HSCAN`, or `ZSCAN`. These are cursor-based iterators that return a small subset of elements and the next cursor ID.
```bash
# Returns a cursor (e.g., "14") and a list of elements
SCAN 0 MATCH user_* COUNT 1000

# Next call uses the cursor
SCAN 14 MATCH user_* COUNT 1000
```
**Principal Tip**: In `redis.conf`, use `rename-command KEYS ""` to permanently disable the command, shifting the failure left (to development instead of production).

---

## M04: Using Redis as a Primary Source of Truth (No AOF/RDB tuning)

### The Mistake
Using Redis to store critical financial ledgers, assuming it's perfectly durable because AOF (Append Only File) is enabled.

### The Impact
Redis is an in-memory datastore first. Its replication is **asynchronous** by default. Even with AOF set to `appendfsync everysec`, a power failure will result in **1 second of committed data loss**. Furthermore, if a primary crashes and Sentinel promotes a replica, any data the primary accepted but hadn't yet synced to the replica (due to network lag) is permanently gone.

### Detection
```bash
# Check replication lag
redis-cli INFO replication 
# Look at master_repl_offset vs replica offset
```

### The Fix / Decision Matrix

| Requirement | Should I use Redis? | Alternative / Fix |
|---|---|---|
| I can lose 1-2 seconds of data on crash | ✅ Yes | Use AOF with `everysec`. It provides great performance with minor risk. |
| I absolutely cannot lose a single write | ❌ No | Do not use Redis. Use PostgreSQL or Kafka. If you force `appendfsync always`, Redis drops to disk I/O speeds (~500 ops/sec), defeating its purpose. |
| I need to prevent split-brain data loss | ⚠️ CAUTION | Use the `WAIT` command. `WAIT 1 100` forces the client to block until at least 1 replica has acknowledged the write. Note: This breaks Redis availability if replicas fail. |
