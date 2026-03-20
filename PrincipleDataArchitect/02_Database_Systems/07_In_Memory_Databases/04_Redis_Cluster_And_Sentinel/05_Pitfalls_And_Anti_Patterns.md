# Pitfalls and Anti-Patterns: Redis Cluster & Sentinel

## M01: The Hash-Tag Hot Key Meltdown

### The Mistake
Using a Hash Tag `{...}` on a highly volatile, massively accessed variable to ensure you can run atomic multi-key Lua scripts alongside it. For example, tagging every active user's session with a global `{app_state}` hash tag so you can query all users and the app state atomically.

### The Impact
By using `{app_state}` inside 5 million session keys, you bypass the mathematical `CRC16(key)` distribution logic. All 5 million keys hash to a single identical Slot (e.g., Slot `5432`). 
The Master node holding Slot `5432` absorbs 100% of the active traffic, maxing out its single CPU thread, while the other 49 Master nodes in the cluster sit idle. When the hot node crashes from memory/CPU exhaustion, the replica takes over and instantly crashes as well (the Cascading Failure anti-pattern).

### Detection
Use the Redis CLI to calculate hash slots or query cluster info.
```bash
redis-cli cluster countkeysinslot 5432
# If one slot has 90% of your cluster's keys, your Hash Tags are toxic.
```

### The Fix
Abandon the requirement for cross-key atomic transactions in a horizontally scaled system. Distribute keys purely via their natural hash. If you must aggregate data across the cluster, do it asynchronously in the application layer (MapReduce logic).

---

## M02: Deploying an Even Number of Sentinel Nodes

### The Mistake
Deploying exactly 2 Sentinel nodes because you have exactly 2 Redis nodes (1 Master, 1 Replica).

### The Impact
Sentinel relies on Quorum (a strict mathematical majority: `(N/2) + 1`). 
For 2 nodes, Quorum is 2. 
If a physical network cable is cut between Datacenter A (holding Master + Sentinel 1) and Datacenter B (holding Replica + Sentinel 2):
- Sentinel 2 cannot see the Master. It initiates a failover request.
- Sentinel 2 asks for votes. Sentinel 1 is unreachable. Sentinel 2 only has 1 vote out of the required 2 Quorum. 
- The failover permanently aborts. The Replica never promotes. Your application goes down purely due to distributed systems math, despite having perfectly healthy backup hardware in Datacenter B.

### Detection
Check Sentinel configurations:
```bash
redis-cli -p 26379 SENTINEL MASTER mymaster
# Check the 'quorum' flag. If nodes=2 and quorum=2, your system is fragile.
```

### The Fix
Deploy a minimum of **3** Sentinel nodes. The 3rd Sentinel can genuinely run on an empty $5/month Application Server, or a completely unrelated backend server. It just needs to exist purely to break voting ties during partitions.

---

## M03: "Blind" Clients (Ignoring MOVED Redirections)

### The Mistake
Using standard REST/HTTP Load Balancers (like AWS ALB or HAProxy) sitting in front of a Redis Cluster, or using a legacy single-node Redis library (like basic `redis-py` instead of `redis-py-cluster`).

### The Impact
Redis Cluster relies on Smart Clients. If a PHP application queries Node A for a key residing on Node C, Node A does NOT fetch the data for the application. It returns a hard string error: `-MOVED 1400 10.0.1.3:6379`.
If the Application library doesn't understand this string protocol, it treats the word `MOVED` as the actual cached string value or immediately throws an unhandled exception, bringing down production.
If an AWS Load Balancer sits between the App and Redis, the App doesn't know the actual internal IPs of the cluster nodes, rendering the `-MOVED` redirection IP address useless.

### Detection
Application exception logs displaying `(error) MOVED...` instead of parsed data.

### The Fix
Never put traditional network Load Balancers between an Application and a Redis Cluster. Always bind the Application directly to the Redis Cluster using a cluster-aware software library (e.g., `JedisCluster` for Java, `redis-py-cluster` for Python) that actively maintains the `16383` slot map locally.

---

## M04: Excessive Cluster Sync Operations (`cluster-require-full-coverage`)

### The Mistake
Leaving the default Redis Cluster configuration `cluster-require-full-coverage yes` enabled on a 100-node cluster housing non-critical cached thumbnails.

### The Impact
If `full-coverage` is `yes`, Redis Cluster demands that all 16,384 slots must be perfectly healthy and covered by an active Master node for the cluster to accept *any* writes.
If Node 12 dies, and its Replica fails to boot, exactly 163 slots go offline (1% of data).
Because 1% of the slots are missing, the other 99 perfectly healthy Master nodes independently refuse to accept *any* commands for their own healthy slots. The entire globally-scaled cluster shuts down over a single node failure.

### Detection
```bash
redis-cli CONFIG GET cluster-require-full-coverage
```

### The Fix
If you are caching highly transient data (where a cache miss simply falls back to a database), set this to `no`.
```text
cluster-require-full-coverage no
```
If a node containing slots 0-100 dies, requests for those slots will fail, but the other 99% of the cluster will continue serving traffic perfectly normally.
