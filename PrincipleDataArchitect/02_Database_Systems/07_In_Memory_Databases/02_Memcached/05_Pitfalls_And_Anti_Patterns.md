# Pitfalls and Anti-Patterns: Memcached

## M01: Slab Calcification (The LRU Trap)

### The Mistake
Assuming Memcached's LRU applies globally across all memory.

### The Impact
Memcached manages memory strictly per **Slab Class**. If you allocate 10GB of RAM to Memcached, and users suddenly upload 9GB of 12KB avatar endpoints (Slab Class 20), those 9GB become rigidly assigned to Class 20. If user behavior shifts entirely and the application now needs to cache 50-byte JSON tokens (Slab Class 2), Memcached will report that it is out of memory and violently evict active tokens from Class 2. Meanwhile, 9GB of RAM sits completely unused in Class 20 because the pages were already assigned and "calcified".

### Detection
Use the `stats slabs` command via telnet:
```bash
echo "stats slabs" | nc localhost 11211
# Look for slab classes with massive total_chunks but low used_chunks
```

### The Fix
Modern Memcached (1.4.25+) introduces an automated background thread to rebalance slabs. You must ensure it is enabled in your startup flags or `memcached.conf`:
```bash
# Enable the background threads to move empty pages between slab classes
-o slab_reassign,slab_automove
```

---

## M02: Exceeding the 1MB Value Limit

### The Mistake
Sending massive payloads (like complete serialized HTTP responses or heavy serialized objects) to Memcached.

### The Impact
Memcached forcefully restricts the maximum size of a single key-value string to **1MB** (the size of a single Slab Page). Attempting to `set` a 1.2MB JSON blob will result in a hard `SERVER_ERROR object too large for cache` failure. If the application doesn't catch this exception properly, the site crashes.

### Detection
Application exception logs (usually `MemcachedError` in PyMemcache or equivalent client libraries) revealing insertions > 1048576 bytes.

### The Fix
1. **Application Side**: Compress large payloads (e.g., gzip/snappy) before sending them to Memcached. Often, a 1.2MB JSON compresses to 150KB.
2. **Infrastructure Side**: If absolutely necessary, you can override the limit by passing the `-I` (capital i) flag at startup:
   ```bash
   memcached -I 5m   # Increases max item size to 5 Megabytes
   ```
   **Caution**: Changing this significantly alters slab page geometry and can drastically increase wasted padding memory across the cluster.

---

## M03: Accidental Amplification via Unrestricted UDP

### The Mistake
Running Memcached bound to `0.0.0.0` (all interfaces) with UDP enabled on AWS or GCP public subnets.

### The Impact
Memcached uses UDP by default (to save TCP handshake microseconds for `GET` requests). UDP can easily be IP-spoofed. Attackers send a 15-byte request from a spoofed victim IP. Memcached replies with a 1MB payload to the victim. This results in a **51,000x amplification ratio**, turning your internal cache into a weapon of mass destruction that takes down your organization's (or others') infrastructure.

### Detection
Check binding in the process arguments:
```bash
ps aux | grep memcached
# If you see: memcached -p 11211
# AND it is exposed publicly... you are entirely vulnerable.
```

### The Fix
Always bind to `localhost` or a strict private VPC interface. Explicitly disable UDP unless actively needed (and deeply secured).
```bash
# Bind ONLY to local loopback and disable UDP (-U 0)
memcached -l 127.0.0.1 -U 0
```

---

## M04: Connection Exhaustion in Microservice Farms

### The Mistake
Using persistent TCP connections between 5,000 Kubernetes pods and 200 Memcached instances.

### The Impact
$5,000 \times 200 = 1,000,000$ active TCP connections. Every Memcached node suddenly has to maintain 5,000 file descriptors. While Memcached scales horizontally, maintaining thousands of idle TCP sockets drains Linux kernel network stack memory, eventually leading to `OOM_kill` or `Too many open files`.

### Detection
```bash
# On the Memcached node
netstat -an | grep ES | wc -l
# Check for > 10,000 established connections
```

### The Fix / Decision Matrix

| Scale | Connection Count | Architecture Requirement |
|---|---|---|
| Modest | < 2,000 TCP | Standard TCP Persistence. Safe. |
| Large | > 5,000 TCP | Deploy **mcrouter** locally as a sidecar/daemonset. Convert 5,000 application TCP connections to local unix sockets, and let mcrouter multiplex traffic over exactly 1 TCP connection to the destination node. |
| Extreme | > 50,000 TCP | Transition to UDP for `GET` requests entirely (like Facebook) to bypass TCP state machine limits on the cache nodes. |
