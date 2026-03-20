# Interview Angle: Memcached

## Q1: "Memcached vs Redis. When would you strictly choose Memcached over Redis for a greenfield project?"

### What They Are Really Testing
This is the ultimate trap question. In 2024, almost everyone defaults to Redis. The interviewer is testing if you understand the actual mechanical differences at the hardware level, or if you're just following industry trends blindly.

### Senior Engineer Answer
"I would choose Redis 95% of the time because it has persistence, replication, and data structures. I would only choose Memcached if I needed an absolutely dead-simple key-value store just for caching serialized HTML strings, and I didn't want to deal with configuring Redis AOF or RDB parameters."

### Principal Architect Answer
"I would deliberately choose Memcached under three strict physical constraints:
1. **Vertical Multi-threading**: If my cloud constraint dictates maintaining very few massive instances (e.g., 64-core, 512GB RAM VMs). Memcached natively saturates all 64 cores simultaneously serving requests. Redis is strictly single-threaded for execution, meaning to saturate a 64-core machine, I have to run 64 independent Redis processes on different ports, complicating client sharding logic exponentially.
2. **Predictable Fragmentation**: If my cache undergoes extreme churn of variously sized objects. Memcached’s Slab Allocator ensures zero OS-level memory fragmentation. Redis relies on `jemalloc`, which is great, but under severe churn can still suffer from fragmentation over time, requiring CPU-heavy Active Defrag processes.
3. **The UDP Topology**: If I need absolute maximum throughput on `GET` operations inside a secure VPC and want to use UDP to bypass TCP handshake states entirely, akin to Facebook's original architecture."

### Follow-Up Probe
*Interviewer: "How does Memcached handle a node failing compared to Redis?"*
**Answer**: "Memcached has zero concept of replication or failover intrinsically. It is a shared-nothing architecture. If node B out of 10 nodes fails, the consistent hashing ring strictly re-maps 10% of the key space to nodes A and C. That 10% suffers an instant 100% cache miss rate and falls back to the DB. Redis relies on Sentinel or Cluster for active-passive replication to handle failures without backend DB miss spikes."

---

## Q2: "How do you solve the Cache Stampede (Thundering Herd) problem without locking the database?"

### What They Are Really Testing
Can you identify race conditions in concurrent distributed architectures without solving them via naive blocking locks (which destroy performance)?

### Senior Engineer Answer
"A cache stampede happens when a viral cache key expires and 1,000 requests hit the DB at once. To fix it, you can set a global Redis/Memcached lock. The first request gets a cache miss, acquires a `SETNX` lock, and queries the physical DB. The other 999 requests fail to get the lock and sleep/retry loop until the first thread fills the cache."

### Principal Architect Answer
"Using a distributed lock works, but it causes thread stalling on frontend web-servers, tying up valuable application workers while they sleep. 
The optimal solution is **Probabilistic Early Expiration (XFetch)**. We store the value with an extended physical TTL via Memcached, but embed a logical timestamp inside the payload. When an application reads the cache, it analyzes the timestamp. If it is *near* expiration, a mathematical formula (using a random variable) dictates a small, increasing probability that the thread will act as if the cache is expired.
Only exactly *one* thread draws the 'unlucky' random number and asynchronously begins recalculating the DB result in the background. Meanwhile, the other 999 threads continue to serve the slightly stale cache data. This achieves zero DB spikes, and zero application thread stalling."

---

## Whiteboard Exercise: Slab Allocation vs Heap Fragmenting

**Prompt:** Draw why Memcached's slab allocator prevents memory fragmentation compared to standard `malloc()`.

```mermaid
graph TD
    classDef os fill:#2d3436,stroke:#b2bec3,stroke-width:2px,color:#dfe6e9;
    classDef good fill:#00b894,stroke:#55efc4,stroke-width:2px,color:#000;
    classDef bad fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;

    subgraph "Standard Linux Heap (Redis/Malloc)"
        HeapOS[Contiguous Heap Memory]:::os
        F1[Used: 20b]:::bad
        H1[Hole: 6b]:::os
        F2[Used: 120b]:::bad
        H2[Hole: 14b]:::os
        
        HeapOS --> F1
        HeapOS --> H1
        HeapOS --> F2
        HeapOS --> H2
        
        note1>Holes are too tiny to reuse. Slowly causes OS to Out of Memory despite free space.]
    end
    
    subgraph "Memcached Slab Allocator"
        Slab[Slab Class 2 - 120b chunks]:::os
        C1[Chunk 1: 120b\n(Contains 100b value)]:::good
        C2[Chunk 2: 120b\n(Contains 115b value)]:::good
        C3[Chunk 3: 120b\n(Empty/Freed)]:::os
        
        Slab --> C1
        Slab --> C2
        Slab --> C3
        
        note2>Any new 100b item perfectly replaces Chunk 3. Zero fragmentation possible.]
    end
```

**Key talking points for the whiteboard:**
1. Draw the "Swiss Cheese" layout of a standard heap. Explain that when `malloc` frees objects of varying sizes, the returning holes cannot fit larger objects.
2. Diagram the 1MB Memcached page being sliced aggressively into identical chunks.
3. Explicitly state the physics trade-off: The cost of zero fragmentation (Memcached) is wasted padding space (internal fragmentation). The cost of tight packing (Redis) is external fragmentation requiring defragmentation cycles.
