# 🧠 Mind Map – Redis Data Structures

---

## How to Use This Mind Map
- **For Revision**: A dense, 60-second hierarchical compression of Redis internals, C-structs, and memory encodings. Use this before architectural reviews.
- **For Application**: Scan the "Techniques & Patterns" and "Mistakes" sections before designing realtime caching, rate-limiting, or streaming systems.
- **For Interviews**: Drill the 'Interview Angle' and 'Assessment' sections to ensure you can articulate *how* Redis works at the byte level, not just what commands it has.

---

## 🗺️ Theory & Concepts

### 01: The Core Philosophy (Data Structures Server)
- **Origin & Purpose**
  - Created by Salvatore Sanfilippo (antirez) in 2009 for LLOOGG to solve real-time write bottlenecks in RDBMS 
  - Shifts computation (like sorting, intersecting, counting) *to the data layer* rather than retrieving data to compute in the application
  - Not just a "cache" like Memcached, but a remote data structures dictionary
- **Performance Characteristics**
  - Microsecond latency (< 1ms P99)
  - Extreme throughput (150,000+ ops/sec single core)
  - Strict predictability due to a single-threaded event loop architecture
- **The Event Loop**
  - Uses OS-level I/O multiplexing (`epoll` on Linux, `kqueue` on BSD)
  - Commands strictly execute serially, guaranteeing ACID isolation for individual commands without mutex locking overhead
  - Multi-threaded I/O (introduced in Redis 6) offloads network socket parsing, but actual data mutation remains strictly single-threaded

### 02: Global Keyspace (`redisObject`)
- **Structure Header**
  - Every value is wrapped in a 16-byte `redisObject` header
  - Holds `type` (4 bits): String, List, Hash, Set, ZSet
  - Holds `encoding` (4 bits): listpack, hashtable, intset, raw
  - Holds `lru/lfu` timestamp (24 bits) for eviction algorithms
- **Memory Management**
  - Relies on `jemalloc` (default) to prevent severe fragmentation from millions of small struct allocations
  - Custom memory encoding converts transparently based on size limits (e.g., listpack upgrades to hashtable)

### 03: Strings (SDS - Simple Dynamic String)
- **C-String Limitations Resolved**
  - C strings are Null-terminated, preventing O(1) length checks
  - C strings cannot hold binary data containing `\0` (e.g., images, serialized protobufs)
- **SDS Byte Layout**
  - Five struct definitions (`sdshdr5`, `8`, `16`, `32`, `64`) depending on string length
  - Memory header: `len` (used bytes), `alloc` (capacity), `flags` (type identifier)
  - Followed by the contiguous `buf[]` array
- **Mechanical Sympathy**
  - Over-allocates capacity on modification to prevent `realloc()` overhead on subsequent appends
  - Remains backward-compatible with C `libc` functions by intentionally adding a hidden `\0` at the end of the buffer

### 04: Hashes & Lists (Listpack & Quicklist)
- **Listpack (The Ziplist Successor)**
  - Replaced Ziplist in Redis 7 to fix cascading update vulnerabilities natively
  - A highly compact, single contiguous memory allocation for small collections
  - Trades off CPU cycles (O(N) search) to save massive RAM overhead (no pointers)
- **Quicklist**
  - A doubly-linked list of Listpacks
  - Combines the fast O(1) head/tail insertion of linked lists with the memory efficiency of contiguous arrays
  - Controls fragmentation via `list-max-listpack-size` (default -2 / 8KB)

### 05: Sorted Sets (ZSet & Skiplist)
- **Probabilistic O(log N)**
  - Avoids the complex rebalancing rotations of B-Trees or Red-Black trees
  - Nodes assigned random heights (levels) via `zslRandomLevel` with a 25% probability per level (max 32 or 64 levels)
- **Dual Representation**
  - Uses a Dictionary (O(1) mapping of member → score)
  - PLUS a Skiplist (O(log N) ordered traversal)
  - Memory intensive, but offers unparalleled ranking computation speed for real-time gaming or rate limiting

### 06: Advanced Internals: Listpack, Rax, and Bitmaps
- **Bitmaps & Bitfields**
  - Not a distinct type, but String operations (`SETBIT`, `GETBIT`)
  - Optimal for "Daily Active User" flags (12.5MB can track 100M users' status for a day)
- **Rax (Radix Tree)**
  - Used for Redis Streams consumer groups and cluster routing
  - Space-efficient prefix tree for long keys with common prefixes
- **Stream Internals (Macro-nodes)**
  - Streams use a specialized Radix tree of Listpacks
  - Each Rax node points to a Listpack containing multiple stream entries for extreme compression

---

## 🗺️ Techniques & Patterns

### T1: Progressive Rehashing
- **When to use**: Under-the-hood core feature of the Redis Global Dict
- **Step-by-Step Mechanics**
  - Triggered when the load factor reaches 1.0 (or 5.0 during BGSAVE)
  - Redis allocates `ht[1]` at double the size of `ht[0]`
  - Sets the `rehashidx` integer to 0
  - Instead of blocking to copy 50M keys, Redis copies *one bucket* of keys during every subsequent CRUD command
  - A background `serverCron` tick also copies batches during idle time
  - Once complete, `ht[0]` is freed and `ht[1]` becomes `ht[0]`
- **Decision Heuristics**: Entirely transparent. Do not run massive `KEYS *` operations during rehashing
- **Failure Mode**: Heavy use of blocking commands or Lua scripts pausing the event loop while rehashing is mid-flight

### T2: Sliding Window Rate Limiting (ZSet)
- **When to use**: Guarding API endpoints against abuse with strict 1-minute limits per user
- **Step-by-Step Mechanics**
  - Create `ZSET` key `{user_id}:{endpoint}`
  - Generate a UUID for the request
  - `ZREMRANGEBYSCORE` to cull timestamps older than `(now - 60s)`
  - `ZCARD` to count remaining items
  - If < limit: `ZADD` the new request UUID with score = `now`
- **Decision Heuristics**: Group these commands in a Lua script or Redis `MULTI/EXEC` block for atomicity
- **Failure Mode**: Clock drift on application servers sending wildly different Unix timestamps as scores

### T3: HyperLogLog for Distinct Counts
- **When to use**: Tracking daily unique page views. An exact `SADD` of 100M UUIDs would consume 800MB+. 
- **Step-by-Step Mechanics**
  - Run `PFADD daily_views {uuid}`
  - Call `PFCOUNT daily_views`
- **Decision Heuristics**: Trades 100% precision for fixed 12KB memory overhead with a standard error of 0.81%
- **Failure Mode**: Trying to use `SMEMBERS` to retrieve the actual list of UUIDs (HLL is a purely probabilistic hashing estimator; original data is gone)

### T4: Fan-out on Write Caching (Lists)
- **When to use**: Twitter/Social Media timeline feeds for real-time perception
- **Step-by-Step Mechanics**
  - User generates a post
  - Background worker queries user's followers
  - Worker runs `LPUSH user:{follower_id}:timeline {post_id}`
  - Limits list size continuously with `LTRIM user:{follower_id}:timeline 0 800`
- **Decision Heuristics**: Optimal for users with < 10,000 followers.
- **Failure Mode**: The "Justin Bieber Problem." Trying to run 150 million `LPUSH` commands causes catastrophic queue backup. Huge accounts must bypass Push, using Pull at read time.

### T5: Geospatial Indexing (GEO)
- **When to use**: "Find pizza places near me" (within 5km)
- **Mechanics**:
  - Uses `GEOADD` to store lat/long as a 52-bit Geohash integer inside a Sorted Set score.
  - `GEORADIUS` uses the ZSet's logarithmic search to find prefix-matches in the geohash space.

---

## 🗺️ Hands-On & Code

### C01: Hash Table Encoding Trick for Memory
- **The Code Pattern**:
  ```python
  # BAD: 1M keys in standard string representation (heavy memory)
  redis.set("user:1001", json_blob)
  
  # GOOD: Segment into buckets of 500 (fits in a single listpack allocation)
  bucket_id = 1001 // 500  # Bucket 2
  redis.hset(f"users:bucket:{bucket_id}", "1001", json_blob)
  ```
- **Configuration Integration**: Requires `hash-max-listpack-entries 512` (the default) to ensure the bucket uses the highly-compressed listpack byte-array structure instead of spinning up an actual hash table.

### C02: Atomic Stream Consumption
- **The Code Pattern**:
  ```bash
  # Creating a consumer group to ensure messages are distributed
  XGROUP CREATE telemetry_stream pipeline_group $ MKSTREAM
  
  # Reading exactly 1 message and blocking until it arrives
  XREADGROUP GROUP pipeline_group worker_1 BLOCK 5000 COUNT 1 STREAMS telemetry_stream >
  
  # Acknowledging completion to remove from PEL (Pending Entries List)
  XACK telemetry_stream pipeline_group 171829391-0
  ```

### C03: Debugging Object Encodings
- **Command**: `OBJECT ENCODING mykey`
- **Significance**: If your 100-element Hash returns `hashtable` instead of `listpack`, you have an entry $> 64$ bytes (default), doubling memory usage.

---

## 🗺️ Real-World Scenarios

### 01: The Flash Sale Collision (Atomicity)
- **The Trap**: Checking inventory (`GET`) and then decrementing (`DECR`) via two separate application-layer TCP calls.
- **Scale**: E-commerce flash sale dropping 500 units to 2 million concurrent users exactly at midnight.
- **What Went Wrong**: Network latency between the `GET` and `DECR` allows hundreds of threads to see `inventory > 0` simultaneously. Inventory goes to -1450.
- **The Fix**: Use server-side atomicity via Redis Lua scripting (`EVAL`). The script executes as a single unbroken execution boundary on the Redis C-thread, making the check-and-subtract mathematically race-condition proof without locking overhead.

### 02: Github Rate Limiting Saturation
- **The Trap**: Storing user request timestamps as JSON strings in Memcached and overwriting them on every request.
- **Scale**: Billions of API requests from CI/CD runners overloading the cache network bandwidth due to constant large JSON overwrites.
- **The Fix**: Migrated to Redis `INCR` and `EXPIRE`. The operation dropped from a 4KB network round-trip to a 50-byte integer increment operation entirely inside the CPU cache lines.

### 03: The "Wait-for-Ack" Durability Fault
- **Scenario**: Financial ledger in Redis using `WAIT 1 0` for sync replication.
- **Failure**: Replica Acknowledged the write but crashed before flushing its own RDB/AOF. On failover, the "Confirmed" write is physically lost.
- **Resolution**: Combine `WAIT` with `appendfsync always` on replicas (high latency penalty).

---

## 🗺️ Mistakes & Anti-Patterns

### M01: The "KEYS *" Blockage
- **Root Cause**: Developer runs `KEYS cart_*` thinking it behaves like a SQL index query. Redis instead runs a single-threaded O(N) linear scan over 40 million global dictionary keys.
- **Diagnostic**: Application metrics show 10,000% spike in P99 connection timeouts. Redis `SLOWLOG` reveals `KEYS` execution times of 8,000ms.
- **Correction**: Replace with `SCAN 0 MATCH cart_* COUNT 1000` to yield the main thread between small iterative bucket scans. Rename the `KEYS` command to `""` in `redis.conf` for production environments.

### M02: Pipelining OOM (The Output Buffer Swell)
- **Root Cause**: Running 2 million commands in a single TCP pipeline payload to maximize bulk-load throughput.
- **Diagnostic**: Redis crashes via the Linux OOM Killer. `INFO memory` shows `client_longest_output_list` consuming 20GB of RAM.
- **Correction**: Break pipelines into 5,000 to 10,000 command chunks. Redis must buffer every response in memory until the pipeline completes; chunking prevents output buffer overflow.

### M03: The Massive Hash Deletion
- **Root Cause**: Executing `DEL user_historical_data` where the key points to a Hash Table with 5 million fields.
- **Diagnostic**: Main thread blocks entirely for the 3 seconds it takes the C `free()` function to release 5 million discrete allocated pointers.
- **Correction**: Upgrade to Redis 4.0+ and use `UNLINK`. This immediately removes the pointer from the global keyspace (O(1)) and hands execution of `free()` to an asynchronous, background bio-thread.

### M04: Expire Hurricane (Simultaneous Keys)
- **Root Cause**: Setting `EXPIRE` for 10 million keys at exactly the same Unix timestamp (e.g., Midnight).
- **Impact**: Redis background eviction thread hits 100% CPU attempting to prune the keyspace, causing massive P99 latency spikes for active users.
- **Fix**: Add a random "Jitter" (e.g., `expire_time = Base + random(0, 300)`).

---

## 🗺️ Interview Angle

### Architectural Defense (Single-Threaded Context)
- **The Setup**: "Why use Redis when modern CPUs have 64+ cores? Isn't single-threaded a massive design flaw?"
- **The Defense**: Redis is not CPU bound, it is memory and network bound. The mechanical overhead of mutex-locking a global dictionary or concurrent tree traversal for 64 threads destroys the exact microsecond latency we seek.
- **What They're Actually Testing**: Deep understanding of mechanical sympathy, memory structures, and the difference between horizontal (Cluster) vs vertical (Threads) scaling.

### Data Structure Selection Matrix
- **The Question**: "Design a system that tracks the 100 most recently visited pages for a user, maintaining exact ordering."
- **The Answer (Weak)**: "A JSON list pulled to the app, modified, and pushed back."
- **The Answer (Strong)**: "A Redis `LIST`. On page view, run `LPUSH visits:{user_id} {url}` followed immediately by `LTRIM visits:{user_id} 0 99`. This guarantees the collection never exceeds 100 elements utilizing an O(1) operation, maintaining strict chronological memory-bound structure."

### O(1) vs O(N) Complexity
- **The Question**: "Is `SISMEMBER` faster than `LINDEX` at index 50,000?"
- **The Answer**: "Yes. `SISMEMBER` is O(1) (Hash Table lookup). `LINDEX` is O(N) (Linked list traversal), meaning it must touch 50,000 pointers manually to reach the data."

---

## 🗺️ Assessment & Reflection

### Knowledge Check Criteria
- [ ] Can you diagram the 16-byte `redisObject` header on a whiteboard?
- [ ] Can you explain why C strings fall short and what SDS `sdshdr8` fixes?
- [ ] Can you walk through exactly what happens when `rehashidx` increments during progressive rehashing?
- [ ] Do you know what `ZSKIPLIST_P = 0.25` calculates intuitively?
- [ ] Can you articulate why `jemalloc` is superior to `libc malloc` for Redis?
- [ ] Diagram the SDS `len` and `flags` fields.

### Production Audit Questions
- Does my local `redis.conf` have `KEYS` renamed to protect against accidental scans?
- Am I utilizing pipelines (in blocks of 10K) effectively, or doing single round-trip `SET` commands in loops?
- Have I verified that Transparent Huge Pages (THP) is disabled on Linux to prevent 2MB COW overhead during BGSAVE forks?
- Could my giant sets be bitsets/bitmaps? Could I save 95% of my RAM?
- Check `INFO persistence`: Is `aof_delayed_fsync` > 0? (Sign of disk IO bottleneck).

---

### 🔥 Deep Research Flashcards

**Q: What is a "Ziplist"?**
**A**: A legacy contiguous byte array structure used for small lists/hashes. Replaced by `listpack` to prevent cascading update O(N^2) issues.

**Q: Why does Redis use a Skiplist instead of a Balanced Tree?**
**A**: Easier to implement, easier to make concurrent (though Redis is single-threaded, the logic holds), and provides equal O(log N) performance with less rotation overhead.

**Q: What is `lazyfree-lazy-eviction`?**
**A**: A config setting that makes the `EXPIRE` deletions asynchronous (like `UNLINK`) instead of blocking the main thread.

**Q: How does `BITCOUNT` work efficiently?**
**A**: Uses the variable-precision SWAR algorithm (SIMD Within A Register) to count bits in parallel within CPU registers.

**Q: What makes Redis Streams different from Lists?**
**A**: Streams support consumer groups, message IDs, and semi-persistent indexing (`XACK`, `XPENDING`), whereas lists are simple FIFO buffers.
