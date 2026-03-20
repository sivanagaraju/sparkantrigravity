# 🧠 Mind Map – Memcached

---

## How to Use This Mind Map
- **For Revision**: A fast hierarchical review of Memcached architecture, with strong focus on memory allocation and scaling topologies.
- **For Application**: Review the "Techniques & Patterns" specifically for handling Cache Stampedes and TCP connection exhaustion before deploying cache at scale.
- **For Interviews**: Drill the 'Interview Angle' to eloquently describe when you would abandon Redis in favor of Memcached's symmetric multi-threading superiority.

---

## 🗺️ Theory & Concepts

### 01: Core Architecture (The Shared-Nothing Cache)
- **Origin & Purpose**
  - Built by Brad Fitzpatrick (LivJournal, 2003) to offload identical database queries
  - No persistence, no complex structures; strictly binary string blobs
- **Multi-threaded Execution Model**
  - Unlike Redis, Memcached uses `libevent` per core
  - Capable of vertically saturating 64-128 core machines, massively outperforming Redis on single instances
  - Global locks were historically a bottleneck, but modern versions use fine-grained hashing segment locks
- **Distributed Topology**
  - The cache cluster has no awareness of itself
  - Sharding is managed 100% horizontally on the client driver using consistent hashing (`ketama`)

### 02: Space Management (The Slab Allocator)
- **Fragmentation Avoidance**
  - Replaces `malloc`/`free` which cause OS heap exhaustion (external fragmentation) over time
  - Grabs 1MB physical Pages and pre-slices them into strictly uniform chunks
- **Slab Classes**
  - Classes represent chunk sizes (e.g., Class 1 = 96b, Class 2 = 120b)
  - Calculated sequentially by the `Growth Factor -f` (default 1.25x)
- **Physical Reality of Packing**
  - Placing a 105-byte string into a 120-byte chunk creates 15 bytes of permanently wasted RAM (internal fragmentation)
  - Memory is allocated exactly once per Slab Class; a page assigned to Class 2 originally couldn't be reclaimed, creating "Calcification" until automated slab reassignment was introduced.

### 03: Eviction (Segmented LRU)
- **The Historical Problem**
  - A massive background analytics job querying 1M missing keys would blast the global Least Recently Used (LRU) list.
  - Effectively pushed mission-critical active user sessions out of RAM, causing production outages.
- **The HOT/WARM/COLD Solution**
  - Newly inserted keys drop into HOT (10% of memory)
  - If a key reaches the tail of HOT, it drops directly to COLD
  - If a key in COLD is hit twice, it is rescued and promoted to WARM (the active working layer)
  - Background scanning scripts naturally flush from HOT to COLD and out, completely bypassing WARM.

### 04: Extstore (Flash Tiering)
- **Bridging RAM and NVMe**
  - The tradeoff of RAM caching is extreme cost (~$5/GB compared to ~$0.10/GB for SSD)
  - Extstore keeps the hash pointers and small keys in RAM, but flushes values over 1-2KB to local NVMe Flash drives.
- **Mechanism**
  - Thread pauses client connection -> reads block off NVMe -> resumes client
  - Lowers caching infrastructure costs by 90% while maintaining sub-millisecond latencies on NVMe M.2 drives.

### 05: Network Protocol Mechanics
- **Text Protocol (Original)**
  - Human readable (e.g., `set mykey 0 60 5\r\nhello\r\n`)
  - Higher overhead due to string parsing but essential for telnet debugging
- **Binary Protocol (Modern)**
  - Reduces CPU parsing overhead by using fixed-length headers (24 bytes)
  - Supports SASL authentication and quiet commands (pipelining without multiple returns)
  - Prevents injection attacks common in the text protocol
- **UDP Mode (Avoid in Public)**
  - No connection state; used for ultra-high throughput where dropped packets are acceptable
  - Requires `set` operations to be smaller than the MTU (typically 1400 bytes)
  - Primary vector for Reflection DDoS attacks if exposed to the i### 06: Background Maintenance Threads
- **LRU Maintainer**
  - Background thread that moves items between HOT/WARM/COLD segments
  - Prevents the "mutator" threads (workers) from having to do list management overhead
- **LRU Crawler**
  - Scans slabs looking for expired items to free memory proactively
  - Without it, Memcached only frees memory when a slab is full and a new insert occurs (lazy expiration)
- **Hash Table Expansion**
  - Automatically doubles the hash table when load factor > 1.5
  - Uses a background thread to prevent latency spikes on the main request path

### 07: Deep Internals: Slab Allocation Tiers
- **Page Size (-I)**
  - Default 1MB. Increasing this allows for keys up to 128MB but increases "internal fragmentation" for small keys.
- **Wasted Memory (Slack)**
  - Calculation: `(Slab Chunk Size - Value Size)`. In large fleets, 20% slack translates to thousands of dollars in wasted cloud spend.
- **Slab Automove**
  - The process of re-assigning physical memory pages from one slab class to another based on real-time cache pressure.

---

## 🗺️ Techniques & Patterns

### T1: CAS (Compare and Swap)
- **When to use**: Appending data (like JSON history) natively where multiple application servers might overwrite each other simultaneously.
- **Step-by-Step Mechanics**
  - Server A executes `gets key`; Memcached returns `VALUE` and a 64-bit `CAS_TOKEN_1`.
  - Server A spends 2ms computing the modified value.
  - Server A executes `cas key new_value CAS_TOKEN_1`.
  - Memcached checks if `Token == 1`. If yes, it writes and token becomes `2`.
- **Failure Mode**: Server B wrote during the 2ms computation. `cas` detects Token is now `2`, returning `EXISTS` (failure), forcing Server A to retry from scratch.

### T2: Consistent Hashing Ring (Ketama)
- **When to use**: Routing keys to caches across 50 nodes, where adding/losing a node shouldn't invalidate 100% of the cache.
- **Step-by-Step Mechanics**
  - Run node IP addresses through `md5` to map them onto a theoretical 0-360 degree ring.
  - Run the string `key` through `md5` to map it to degrees.
  - Traverse the ring clockwise until intersecting a Node IP point.
- **Failure Mode**: When a node fails, 1/N of keys are rerouted clockwise. The subsequent node absorbs an immediate 2x traffic spike, potentially cascading into failure. Avoid via virtual nodes (many points per IP).

### T3: Probabilistic Early Expiration (XFetch)
- **When to use**: Heavy backend aggregations suffering from Cache Stampedes upon key TTL expiration.
- **Step-by-Step Mechanics**
  - Embed the creation timestamp inside the cached string.
  - Give Memcached a massive artificial TTL (e.g., 2 hours).
  - App pulls data. If Application Time is near logical TTL, roll a random exponential variable.
  - If calculation hits, intentionally act as if cache is missed, and rebuild in background thread.
- **Decision Heuristics**: Requires tuning the `beta` and `computation_delta` variables to match workload intensity.
- **Failure Mode**: If `delta` is set too aggressively for fast-changing data, data appears permanently stale.

### T4: Leased Get (Gutter Pool)
- **When to use**: Mitigating "Cold Cache" saturation when a new cluster node is added.
- **Mechanism**:
  - Request misses in the primary cluster.
  - Client attempts to read from a secondary "Gutter" cluster (small, cheap nodes).
  - Prevents the DB from being slammed by absolute cache misses during rebalancing.

### T5: Multi-Tier Caching (L1/L2)
- **Strategy**: 
  - L1: Local In-Memory Cache (Guava/Caffeine) on the Application Server (microsecond latency).
  - L2: Distributed Memcached (millisecond latency).
  - Keeps extremely hot "global" keys (like config flags) from saturating the network.

---

## 🗺️ Hands-On & Code

### C01: Instantiating with Reassignment and Segmented LRU
- **The Code Pattern**:
  ```bash
  # Launch command tuned for production
  memcached -m 12000 -l 10.0.1.5 -U 0 -o slab_reassign,slab_automove,lru_maintainer
  ```
- **Explanation**: Binds to private VPC (prevents UDP DDoS), allocates 12GB RAM, allows background threads to prevent Slab Calcification, and activates the HOT/WARM/COLD LRU algorithm.

### C02: Basic Application-Side Sharding
- **The Code Pattern**:
  ```python
  from pymemcache.client.hash import HashClient
  # Client library applies Ketama Consistent Hashing natively
  mc = HashClient([('10.0.1.1', 11211), ('10.0.1.2', 11211)])
  mc.set('my_key', 'some_value')
  ```

### C03: Monitoring Slabs and Fragmentation
- **The Command**: `echo "stats slabs" | nc localhost 11211`
- **Output Analysis**:
  - `active_slabs`: Total number of classes being used.
  - `total_pages`: Total 1MB pages assigned.
  - `used_chunks`: Actual utilization.
  - `free_chunks_end`: Chunks available at the end of the last page (indicates rebalancer health).

### C04: Inspecting Hot Keys
- **The Command**: `echo "lru_crawler metadump all" | nc localhost 11211`
- **Purpose**: Dumps the metadata of all keys (keys, TTLs, slab classes) without hitting the keyspace yourself.

---

## 🗺️ Real-World Scenarios

### 01: The UDP Amplification DDoS Vector
- **The Trap**: Leaving Memcached bound to `0.0.0.0` with UDP (-U) enabled on a cloud instance.
- **Scale**: GitHub 2018 Attack hitting 1.35 Tbps of incoming saturation.
- **What Went Wrong**: UDP requires no handshake. Attacker faked IP packets looking like they came from GitHub, requested a 1MB payload from a naive Memcached server, generating a 51,000x volumetric amplification reflection wave.
- **The Fix**: Default configuration changed to bind local and drop UDP globally.

### 02: Facebook Mcrouter Geometry
- **The Trap**: 10,000 Web Servers making PHP array calls directly to 1,000 Memcached servers.
- **Scale**: 10,000,000 active persistent TCP connections per server destroying the Linux Networking Stack memory.
- **The Fix**: Abstracting routing to a sidecar (`mcrouter`). Web Server opens 1 local socket to `mcrouter`. `mcrouter` opens 1 robust multiplexed TCP connection to the destination caching node.
- **Advanced Routing**: `mcrouter` can perform "Shadowing" where it sends 1% of production traffic to a test cluster to verify performance before a rollout.

### 03: Twitter's Snowflake (Caching IDs)
- **Scenario**: Generating 64-bit unique IDs across globally distributed data centers.
- **Role**: Memcached was used to cache the "Worker ID" and "Datacenter ID" locally to avoid Zookeeper/Etcd round-trips for every tweet.

### 04: The "Stale-While-Revalidate" Pattern
- **Problem**: Key expires, and the next 1,000 users all see a 404/Empty state while the server regenerates the data.
- **Resolution**: Use the probabilistic early refresh to start regeneration *before* the key physically disappears from Memcached.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Slab Calcification Crash
- **Root Cause**: Memory profile shifts from large 5KB HTML blobs to tiny 50b JSON blobs over a week.
- **Diagnostic**: You hit `OOM` and high eviction counters on Class 2, despite only consuming a total of 15% of the overall 10GB allocated to the system (8GB is stuck in Class 30 unused).
- **Correction**: Restart with `slab_reassign` threads activated.

### M02: Pushing Items Larger than 1MB
- **Root Cause**: Code deploys a feature caching whole Base64 encoded PDF reports indiscriminately.
- **Diagnostic**: Error logs scream `object too large for cache`.
- **Correction**: Implement gzip/snappy compression wrapping at the Python/Node library level. Binary compresses exceptionally well and easily sneaks under the 1MB max page limit.

### M03: Ignoring TCP Incast
- **Problem**: 100 parallel workers requesting data from 1 Memcached node at the exact same millisecond.
- **Result**: Small packets saturate the network switch buffer, leading to dropped packets and 500ms tail latency spikes.
- **Fix**: Use `mcrouter` or implement jitter on the application side to desynchronize requests.

### M04: Using Memcached for Sessions (Persistence Trap)
- **Problem**: Storing critical login sessions in Memcached.
- **Result**: A server restart or even a simple cache eviction logs out thousands of users.
- **Fix**: Sessions belong in a data store with persistence (Redis AOF/RDB or SQL).

---

## 🗺️ Interview Angle

### Single-Threaded vs Multi-Threaded Physics
- **The Setup**: "Why did Netflix build EVCache on Memcached instead of Redis?"
- **The Defense**: Redis requires complex multi-process sharding (Redis Cluster / Twemproxy) to scale over 150k ops/sec on a modern 32-core server. Memcached's natively multi-threaded Event Loop architecture allows a single monolithic background process to blast millions of ops/sec across 32 cores effortlessly, maintaining architectural simplicity.
- **What They're Actually Testing**: Complete disregard for marketing trends, exposing exact CPU execution modeling knowledge.

### Explaining P99 Latency Spikes
- **The Question**: "Why do standard LRU caches suffer extreme miss rates during night-time database backups?"
- **The Answer**: "A batch job scanning user tables heavily reads through the cache mapping, pushing hot daytime keys over the tail edge of a traditional LinkedList LRU. Memcached solves this mechanically via Segmented LRU; the batch scan traverses the 'HOT' queue directly to the 'COLD' queue and flushes without ever polluting the 'WARM' working memory."

### Consistency Trade-offs
- **The Question**: "Is Memcached eventually consistent or strongly consistent?"
- **The Answer**: "Memcached is a single-node strongly consistent store (linearizable for that node). However, in a distributed cluster with replication, it is typically used as a 'Lookaside' cache, meaning consistency is the responsibility of the application. If many apps update the DB but fail to invalidate the cache, you get stale data. Use CAS tokens to achieve atomicity at the cache level."

### Warmup Strategies
- **The Question**: "How do you handle a new cache node join without crashing the DB?"
- **The Answer**: "I would employ a 'Soft-Launch' or 'Gutter' strategy. The client library hashes to the new node; on miss, it checks the old node or a gutter pool before hitting the DB. Alternatively, use mcrouter's 'prefix migration' to slowly ramp traffic to the new segment."

---

## 🗺️ Assessment & Reflection

### Knowledge Check Criteria
- [ ] Can you define exactly why Slab Allocation causes internal wasted space?
- [ ] Do you understand why setting `-I 5m` changes the geometry of pages?
- [ ] Can you diagram the XFetch probabilstic algorithm graph to avoid Stampedes?
- [ ] Could you explain `CAS_TOKEN` behavior using a timeline sequence diagram?
- [ ] Do you know what `active_slabs` vs `total_pages` indicates about memory health?
- [ ] Explain the difference between `evictions` and `reclaims` in `stats` output.

### Production Audit Questions
- Run `ps aux | grep memcached` on my fleet. Are any servers open to UDP 11211 natively?
- Are we catching `MemcachedError` explicitly when users generate payloads > 1MB?
- Have we tuned our `HashClient` to employ consistent hashing, or are we mapping array indexes `key % nodes` (which breaks on scale down)?
- Is `mcrouter` configured to handle cold-start warmup of new nodes?
- Check `stats items`: Is `evicted_time` < 3600? (Your cache is too small for your working set).

---

### 🔥 Deep Research Flashcards

**Q: What is the maximum key length in Memcached?**
**A**: 250 bytes in the text protocol; up to 65k in the binary protocol (though rare/unrecommended).

**Q: Why does Memcached use `libevent`?**
**A**: To achieve non-blocking I/O multiplexing across multiple worker threads, allowing one thread to wait on a socket while others process instructions.

**Q: What is the growth factor `-f`?**
**A**: It determines the size difference between sequential slab classes. If `f=1.25`, Class 1 is 96b, Class 2 is 120b (96 * 1.25).

**Q: How does `slab_automove` work?**
**A**: It monitors the eviction rates of different slab classes. If one class has consistent OOM evictions and another has free pages, it transparently moves a 1MB page between them.

**Q: What happens if you use `set` with a TTL of 0?**
**A**: The item never expires by time, but it can still be evicted if the cache runs out of memory.

**Q: What is "Memcache Mutation"?**
**A**: The act of using `incr`, `decr`, `append`, or `prepend` to modify values inside the server without a full round-trip `get` and `set`.

**Q: How does mcrouter handle "All-Async" replication?**
**A**: It sends the write to all replicas but doesn't wait for confirmation. Optimal for speed; risky for consistency.
e evicted if the cache runs out of memory.
