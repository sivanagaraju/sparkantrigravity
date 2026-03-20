# 🧠 Mind Map – Redis Cluster & Sentinel

---

## How to Use This Mind Map
- **For Revision**: Review the stark architectural differences between Active-Passive (Sentinel) and Active-Active (Cluster). Focus on the definition of a Hash Slot.
- **For Application**: Audit your production environment using the "Mistakes & Anti-Patterns" branch to ensure you don't have exactly two Sentinels executing your critical failovers.
- **For Interviews**: Use the 'Interview Angle' to articulate exactly how Smart Clients handle CRC16 modulo redirection logic.

---

## 🗺️ Theory & Concepts

### 01: Core Architecture Differences
- **Sentinel (High Availability Only)**
  - Topology: 1 Active Master, multiple Read-Only Replicas.
  - Scale: Bounded by the RAM and CPU of exactly 1 server.
  - Failover: Handled by external `redis-sentinel` daemon processes.
- **Cluster (High Availability + Horizontal Sharding)**
  - Topology: Multiple Active Masters, Multiple passive Replicas.
  - Scale: Combines RAM across 1,000 servers. CPU scales perfectly linearly.
  - Failover: Master nodes natively monitor each other via the Gossip Protocol. No separate daemons required.

### 02: Quorum & Split-Brain (Sentinel)
- **The Definition of Quorum**
  - The strict majority vote required to promote a replica safely (`V > N/2`).
  - Deploying 3 Sentinels ensures Quorum is 2. Deploying 5 ensures Quorum is 3. 
- **Split-Brain Physics**
  - If a datacenter splits, a minority island of nodes physically cannot override the global architecture.
  - Sentinel prevents two Masters from booting dynamically. However, without configuring `min-replicas-to-write 1`, the isolated old Master will temporarily continue accepting dark user writes.

### 03: Hash Slots (Cluster)
- **The Modulo Math**
  - The cluster space is divided into exactly **16,384** Hash Slots.
  - When storing `user:10`, Redis parses `CRC16("user:10") % 16384` to arrive at a slot number (e.g., Slot 1024).
- **Slot Ownership**
  - Master 1 claims Slots 0 to 5000. Master 2 claims 5001 to 10000.
  - If a key hashes to 1024, it must structurally be stored strictly on Master 1.
- **Hash Tags `{}`**
  - Using `{account:99}:history` and `{account:99}:profile`.
  - The hash algorithm completely ignores the text outside the braces, evaluating only `CRC16("account:99")`.
  - Both keys map to exactly the same slot, guaranteeing they land on the exact same physical Master node, enabling fast multi-key Lua scripts.

### 04: The Gossip Protocol & Epochs (Cluster)
- **The Cluster Bus**
  - Every Node opens a secondary port (Client Port + 10000, i.e., 16379).
  - Nodes exchange `PING`/`PONG` binary packets continuously sharing their view of the cluster state.
- **Configuration Epochs**
  - A monotonically increasing integer ID representing the authoritative timeline.
  - If Master A says "Replica B is the new master (Epoch 7)" and Node C says "Replica B is master (Epoch 9)", the cluster natively defers immediately to Epoch 9's version of reality.

### 05: Client-Side Caching (Redis 6+)
- **Tracking Mode**
  - Redis Master tracks which keys a client has read.
  - If a key changes, Redis pushes an invalidation message to the client.
  - Client clears its local memory cache (L1), reducing total network RTT to zero for subsequent hits.
- **Scaling Benefits**
  - Offloads read IOPS from the massive cluster to the thousands of cheap app-server RAM chips.

### 06: Data Persistence in Distributed Contexts
- **AOF (Append Only File) & RDB**
  - Every Master and Replica manages its own local persistence files.
  - Resharding involves RDB transfers between nodes implicitly.
- **fsync Policy in Clusters**
  - Performance vs Safety: `appendfsync everysec` is standard.
  - Risk: If a Master crashes, 1 second of writes may be lost, even if acknowledged to the client (Wait-for-ACK logic is eventual).

### 07: Security & Access Control (ACLs)
- **Cluster Authenticity**
  - All nodes must share a uniform `masterauth` and `requirepass`.
  - The Cluster Bus itself should be TLS encrypted to prevent Gossip tampering.
- **ACL Sharding**
  - Clients can be restricted to specific keyspaces (e.g., `user:*`).
  - Sentinel can use distinct ACL users to perform failovers without having root DB access.

### 08: Deep Dive: Topology Awareness & Failure Domains
- **Physical Rack Layouts**
  - Masters and their direct Replicas MUST NOT share the same physical rack or chassis.
  - Use `cluster-announce-bus-port` and orchestrators (like Kubernetes Operators) to enforce anti-affinity.
- **Data-Center Awareness**
  - Sentinel deployments spanning 3 Datacenters (A, B, C) ensure that even if one full DC collapses, the majority (2/3) can safely declare a new master in a surviving DC.

### 09: The 16384 Hash Slot Limit (Deep Internal)
- **Why 16,384?**
  - The cluster topology is shared via Gossip packets. 
  - Using 16k slots allows the slot-mapping bitmap to fit in exactly 2KB. 
  - If Redis used 65k slots (as sometimes proposed), the heartbeat packets would bloat, causing "Gossip Storms" and CPU spikes on large clusters.
  - 16k provides enough granularity for 1,000 nodes while keeping constant-time bitmap comparison extremely fast in the Index Server kernel.

---

## 🗺️ Techniques & Patterns

### T1: Smart Client Routing
- **When to use**: Connecting any backend application to Redis Cluster.
- **Step-by-Step Mechanics**
  - Application boots. Client library natively connects to *any* available Redis node.
  - Client issues `CLUSTER SLOTS` to download the entire routing blueprint.
  - App triggers `GET key`.
  - Client locally hashes the key, looks up the Slot mapping, and opens a direct TCP connection.
- **Failure Mode**: Using naive clients like Python `redis`. The simple client hits the wrong node, receives a `-MOVED` error string, and crashes trying to parse it as UTF-8 data.

### T2: Live Resharding
- **When to use**: High Season (e.g., Black Friday) requires shifting from 10 Masters to 15 Masters.
- **Step-by-Step Mechanics**
  - Boot 5 empty nodes. Join them to the cluster geometry (`cluster meet`).
  - Run the resharding tool to calculate a balanced slot layout.
  - Redis initiates background memory copying from Node 1 -> Node 15.
  - While migrating, Node 1 responds to client queries spanning transitioning data with `-ASK`.
  - Client transparently hops to Node 15 to fulfill exactly that transient request.

### T3: Redlock (Distributed Locking)
- **When to use**: Guaranteeing a lock across a distributed environment where a single master failure shouldn't release the lock.
- **Mechanism**:
  - Client tries to acquire lock in N/2 + 1 masters (e.g., 3 out of 5).
  - Uses the same clock-drift-aware timeout for all requests.
  - If it wins the majority before expiration, it holds the lock.

### T4: Replica Migration (Automatic Rebalancing)
- **When to use**: A master loses all its replicas due to chain failures.
- **Mechanism**:
  - A master with "too many" replicas (e.g. 3) notices another master is "naked" (0 replicas).
  - One of the extra replicas automatically migrates (re-points) to the naked master.
  - Feature: `cluster-allow-replica-migration yes`.

---

## 🗺️ Hands-On & Code

### C01: Dynamic Failover Testing (Sentinel)
- **The Process**:
  - `redis-cli -p 26379 sentinel failover mymaster`
  - Monitor logs: `+sdown` -> `+odown` -> `+try-failover` -> `+promoted-slave` -> `+config-update-from`.
- **Validation**: High availability verification isn't complete until the Application side transparently reconnects to the new IP.

### C02: Cluster Rebalancing CLI
- **The Command**:
  ```bash
  redis-cli --cluster rebalance 10.0.1.1:6379 --cluster-use-empty-masters
  ```
- **Explanation**: Automatically shifts slots from saturated nodes to the 5 newly added empty nodes.

### C03: Monitoring Cluster Health
- **Command**: `redis-cli -p 6379 cluster info`
- **Metric Criticality**:
  - `cluster_state: ok`: If `fail`, the entire cluster stops responding to queries.
  - `cluster_slots_assigned: 16384`: Must be 16384. If lower, data is being lost in "zombie" slots.

### C04: Manual Failover (Cluster)
- **The Command**:
  ```bash
  redis-cli -p 6379 CLUSTER FAILOVER [FORCE|TAKEOVER]
  ```
- **Explanation**:
  - `FORCE`: Failover without checking for master connectivity (useful if master is dead).
  - `TAKEOVER`: Promote replica without consensus (EXTREME DANGER, use only in total cluster partitioning recovery).

---

## 🗺️ Real-World Scenarios

### 01: The Hash-Tag CPU Spike
- **The Trap**: Using a hyper-generic global Hash Tag for all application elements.
- **Scale**: E-commerce website launching 100,000 queries per second.
- **What Went Wrong**: An engineer tagged inventory keys as `item_id:{global}`. Every single inventory item explicitly mapped mathematically to a single identical Slot (Slot 8000). The specific physical server holding Slot 8000 saturated to 100% CPU usage and OOM'd.
- **The Fix**: Remove the `{global}` tag. Accept that cross-slot logic is impossible at scale.

### 02: GitLab's Partial Network Partition
- **The Trap**: Running an even number of Sentinel node orchestrators.
- **Scale**: Global platform hosting critical git objects.
- **What Went Wrong**: Network switch failure isolated one Sentinel. Because Quorum required 2, and the surviving isolated branch had only 1, the failing Master was never legally able to be voted out. 
- **The Fix**: Enforced minimal topology requirements of 3 isolated availability zones.

### 03: The Cluster Multi-ACK latency
- **Problem**: Enabling `WAIT 3 1000` for critical financial transactions in a cluster.
- **Result**: P99 latency jumps from 1ms to 50ms.
- **Tradeoff**: Explicitly trade availability-speed for durability-safety.

### 04: The "Gossip Storm" Failure
- **Scenario**: A 500-node cluster experiencing intermittent packet loss on the internal bus.
- **Symptom**: Random nodes falsely reporting siblings as `PFAIL`. Failover voting starts every few seconds, causing constant topology flux.
- **Fix**: Tune `cluster-node-timeout` to 15s+ and optimize internal VLAN MTUs to prevent packet fragmentation.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Load Balancing Redis Cluster
- **Root Cause**: Infrastructure team deploys an NLB/F5 uniformly over the IP addresses of the 10 Cluster Masters.
- **Diagnostic**: App asks NLB for key. NLB hits Master 4. Master 4 returns `-MOVED`. App can't see the target IP because it's hidden behind the NLB.
- **Correction**: Disband Load Balancers. Use Smart Clients.

### M02: Massive `KEYS *` Analytics in Cluster
- **Root Cause**: Running slow scan commands across a sharded interface.
- **Diagnostic**: `KEYS *` only scans the specific node you are connected to (returning 1/Nth of data).
- **Correction**: Aggregate scanning by firing independent commands to all Masters.

### M03: Two Sentinels Topology
- **Reality**: You deploy 1 Master, 1 Replica, and 2 Sentinels.
- **Fault**: If Sentinel 2 crashes, 1 remains. Quorum is 2. Failover is impossible.
- **Fix**: Always odd numbers (3, 5, 7).

### M04: Mixing Instance Sizes in Cluster
- **Problem**: Master A has 64GB RAM, Master B has 8GB RAM.
- **Result**: Data is distributed by Hash Slot count, NOT memory capacity. Master B will OOM and evict data while Master A is 90% empty.
- **Fix**: All Cluster Masters must have identical vertical specs.

---

## 🗺️ Interview Angle

### Single-Thread Performance Scaling
- **The Setup**: "How can Redis process 5 Million Operations per Second if node execution is strictly bound to a single CPU?"
- **The Defense**: Redis execution is bound to one core, but Redis Cluster establishes a mathematically isolated matrix. By deploying 50 distinct isolated Master nodes, the client library is distributing processing across 50 fundamentally disconnected CPUS via CRC16 math.

### Multi-Key Restrictions
- **The Question**: "Why can't I run a `SUNION user1:friends user2:friends` in Redis Cluster?"
- **The Answer**: "`user1` and `user2` statistically hash to two disparate nodes. Redis enforces Shared-Nothing processing. To bypass this, we utilize Hash Tags `{user1}:friends` and `{user1}:meta` to force collision onto a uniform hash slot."

### Gossip Overhead
- **The Question**: "Why shouldn't I build a 5000-node Redis Cluster?"
- **The Answer**: "The Gossip Protocol overhead. In a 5000-node cluster, the heartbeat traffic would consume more bandwidth than the actual database commands. Most production clusters cap at ~400 nodes."

---

## 🗺️ Assessment & Reflection

### Knowledge Check Criteria
- [ ] Diagram the Raft-style failover mechanism and Quorum logic.
- [ ] Understand CRC16 mod 16384 implications on key distribution.
- [ ] Difference between permanent `-MOVED` and transient resharding `-ASK`.
- [ ] Pinpoint why Hash Tags are a double-edged sword (OOM risk).
- [ ] Define `S_DOWN` vs `O_DOWN` in Sentinel.

### Production Audit Questions
- Run `redis-cli --cluster check <node>`. Any orphan slots or masterless replicas?
- Are we using `replica-ha-priority` correctly to ensure the strongest hardware is promoted first?
- Is `cluster-require-full-coverage` set to `no` to prevent whole-site outages during a single node loss?
- Do our app client logs show frequent `MOVED` events? (Indication of constant topology churn).

---

### 🔥 Deep Research Flashcards

**Q: What is a "Hash Slot"?**
**A**: One of 16,384 logic segments that keys are mapped to via CRC16.

**Q: What happens if a Master fails without any Replicas in Cluster?**
**A**: If `cluster-require-full-coverage` is `yes`, the entire cluster shuts down for safety.

**Q: How does a client handle a `-MOVED` error?**
**A**: Updates its local `Slot -> IP` cache and retries the command on the new node.

**Q: What is a "Configuration Epoch"?**
**A**: A version number for the cluster topology. Higher epochs override lower ones during Gossip conflicts.

**Q: Why use `WAIT`?**
**A**: To block the caller until the write is replicated to N slaves, ensuring stronger consistency.

**Q: What is the benefit of the `READONLY` command in a replica?**
**A**: Allows a cluster-aware client to read from a replica node for a specific connection.

**Q: What is `cluster-migration-barrier`?**
**A**: The minimum number of replicas a master must retain before one of its "extra" replicas is allowed to migrate to a failing master.
