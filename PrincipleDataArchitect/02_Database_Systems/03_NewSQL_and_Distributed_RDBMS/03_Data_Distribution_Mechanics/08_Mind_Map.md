# 🧠 Mind Map – Data Distribution Mechanics

---

## How to Use This Mind Map
- **For Revision**: Review the Theory and Mistakes sections before reading the deep dives to refresh your mental model.
- **For Application**: Use the Techniques & Patterns section to align your product requirements to the correct distribution strategy (Hash vs Range).
- **For Interviews**: Rehearse the Whiteboard patterns and the Interview Angle questions to quickly formulate strong, structured answers.

---

## 🗺️ Theory & Concepts

### Range Sharding
- **Definition**
  - Data is split into contiguous, sorted segments based on the partition key.
- **Mechanism**
  - The key space is divided into ranges (e.g., `[A-C)`, `[C-F)`).
  - A metadata routing layer tracks which physical node owns which range.
- **Why it matters**
  - It allows for highly efficient range scans (`BETWEEN x AND y`), as sorted data is co-located.
- **Key metrics**
  - CockroachDB splits ranges automatically when they exceed 64MB or 512MB default limits to prevent single-range overload.

### Hash Sharding
- **Definition**
  - Data is distributed uniformly across shards using a hash function on the partition key.
- **Mechanism**
  - The routing layer hashes the key and computes `modulo N_nodes` to pinpoint the specific physical node.
- **Why it matters**
  - It guarantees an even distribution of data and write loads, neutralizing the risk of hotspots.
- **Key metrics**
  - Range scans are impossible; any query without the exact partition key devolves into a cluster-wide "scatter-gather" operation.

### Consistent Hashing
- **Definition**
  - A hash topology mapped onto a virtual ring (e.g., $0$ to $2^{64}-1$), drastically minimizing data reshuffling.
- **Mechanism**
  - Both data keys and node identifiers are hashed onto the ring. A key maps to the first node encountered moving clockwise.
- **Why it matters**
  - When nodes are added or removed, only $1/N$ of the data moves (the fraction owned by the adjacent node), preventing catastrophic network-level reshuffling.
- **Key metrics**
  - Virtual nodes (vnodes) are layered on physical servers (often 256 vnodes per physical server in Cassandra) to balance load across heterogeneous hardware capabilities.

---

## 🗺️ Techniques & Patterns

### T1: Hash-Prefixing Monotonic Keys
- **When to use**: When your business logic requires sequential/auto-incrementing primary keys but your database is range-partitioned.
- **Step-by-Step**
  - 1. Extract the sequential ID.
  - 2. Compute a hash of it.
  - 3. Prefix the ID with `Hash % N` to act as a virtual bucket.
  - 4. Set the Primary Key as `(bucket_id, sequential_id)`.
- **Decision heuristics**: Only use if you absolutely cannot migrate the underlying system to use UUIDv4s.
- **Failure Mode**
  - If the bucket modulo is too small, you still create localized hotspots. If too large, reading sequential ranges becomes incredibly slow across many shards.

### T2: Declarative Time-Based Partitioning
- **When to use**: Managing massive timeseries data (e.g., clickstreams, telemetry) where old data must be purged quickly.
- **Step-by-Step**
  - 1. Create a parent partitioned table in Postgres.
  - 2. Define ranges explicitly by month or week.
  - 3. Route inserts to the parent, which delegates to the physical partition child.
- **Decision heuristics**: Perfect for data lifecycle management (e.g., dropping a 50GB month-partition is instantaneous compared to a massive `DELETE` statement).
- **Failure Mode**
  - Forgetting a cron job to create the upcoming month's partition will cause catastrophic unhandled write exceptions on the exact moment the month rolls over.

---

## 🗺️ Hands-On & Code

### C1: CockroachDB Geo-Partitioning DDL
- **Pattern**: `ALTER PARTITION 'eu' OF INDEX users@primary CONFIGURE ZONE USING constraints = '[+region=eu]';`
- **Impact**: Pins ranges explicitly to physical Availability Zones, ensuring European data physically resides on European servers for GDPR compliance and local read latency.

### C2: Cassandra Hash Partitioning DDL
- **Pattern**: `PRIMARY KEY ((tenant_id, month), event_time)`
- **Impact**: Uses a composite partition key. The double parentheses force both `tenant_id` and `month` to generate the hash. `event_time` is the clustering key, sorting the data sequentially on the disk for that specific tenant/month combination.

---

## 🗺️ Real-World Scenarios

### 01: Instagram PostgreSQL Logical Sharding
- **The Trap**: Mega instances hit hardware vertical scaling limits (RAM/EBS IOPS maxed out).
- **Scale**: Hundreds of millions of uploads per day.
- **The Fix**: Embedded a 13-bit logical shard ID into a 64-bit auto-generated image ID using PL/pgSQL. The app layer routes requests explicitly to physical servers hosting the logical chunks.

### 02: Discord MongoDB to ScyllaDB Migration
- **The Trap**: MongoDB replica-set primaries couldn't handle the write throughput of a globally growing chat architecture.
- **Scale**: Billions of messages read and written per day.
- **The Fix**: Moved to Cassandra (Hash partition by channel + message ID) to distribute writes perfectly. Eventually migrated from Cassandra to ScyllaDB to escape JVM garbage collection latency spikes.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: The Scatter-Gather Death Spiral
- **Root Cause**: Querying an unindexed attribute without passing the Partition Key.
- **Diagnostic**: Look for `Select * from events where status = 'ACTIVE'`. If `status` isn't the partition key, the coordinator broadcasts the query to 1,000 nodes.
- **Correction**: Introduce Global Secondary Indexes (GSIs) or duplicate the data into a different table hashed by `status`.

### M02: Monotonic Write Hotspots (Range)
- **Root Cause**: Using a timestamp or auto-incrementing integer as the first column of the Primary Key in Spanner or CockroachDB.
- **Diagnostic**: One single node spikes to 100% CPU utilization while the rest of the cluster idles at 0%. Write latency skyrockets.
- **Correction**: Switch the Primary Key generator entirely to UUIDv4, scattering the inserts across all nodes identically.

### M03: The Fat Partition
- **Root Cause**: Sharding entirely by a B2B `tenant_id` where one enterprise customer is 10,000x larger than a standard customer.
- **Diagnostic**: Disks on specific physical nodes fill up. Rebalancing fails due to network payload sizes.
- **Correction**: Partition Key Salting. Add a virtual bucket to the key: `(tenant_id, salt(event_id))`.

---

## 🗺️ Interview Angle

### Q: Adding Capacity to a Cluster
- **The Setup**: "How do you add 10 nodes to a running 10-node cluster right before Black Friday?"
- **The Secret Trap**: They are testing if you know that moving data across a network is incredibly expensive.
- **Strong Answer**: Explain Consistent Hashing and virtual nodes. Emphasize that adding nodes forces massive Disk I/O and Network bandwidth as SStables are streamed to new nodes. If you do this *during* Black Friday, you will crash the cluster. It must be done weeks in advance.

### Q: The Viral Celebrity Write Storm
- **The Setup**: "A celebrity posts a tweet, generating a massive write storm to their specific user ID. How do you prevent the database from melting?"
- **The Secret Trap**: A naive answer suggests Redis caching, which doesn't solve a *write* storm at the storage layer.
- **Strong Answer**: Change the partition scheme from a single `user_id` to a hash of the combined `(user_id, post_id)` to forcibly scatter the writes uniformly across all cluster nodes.

---

## 🗺️ Assessment & Reflection
- [ ] Could you draw a Modular vs Consistent Hash ring from memory?
- [ ] Do you know exactly which databases mandate `UUIDv4` over `Auto-Increment` keys?
- [ ] Can you estimate the network latency cost of a Scatter-Gather query over 30 nodes?
- [ ] **Audit Question**: Check your current production DB. Is there a table where 90% of the read/write load is hitting a single physical partition because of sequential keys or massive tenant skew?
