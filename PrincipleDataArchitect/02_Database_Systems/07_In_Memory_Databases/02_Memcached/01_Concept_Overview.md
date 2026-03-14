# Memcached — Concept Overview

> The simplest in-memory caching layer: key-value, no persistence, multi-threaded.

## Redis vs Memcached

| Feature | Redis | Memcached |
|---|---|---|
| **Data Structures** | Rich (7+ types) | String only |
| **Persistence** | RDB + AOF | None |
| **Threading** | Single-threaded (I/O threads in 6.0+) | Multi-threaded |
| **Memory Management** | Exact (jemalloc) | Slab allocator |
| **Cluster** | Redis Cluster (hash slots) | Client-side sharding |
| **Best For** | Complex data, pub/sub, queues | Simple key-value caching |

**When to choose Memcached**: When you need ONLY simple caching (string key-value), multi-threaded performance on large core counts, and don't need persistence or rich data structures. Facebook used Memcached at scale for their look-aside cache (TAO).

## References

| Resource | Link |
|---|---|
| [Facebook TAO Paper](https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson) | Social graph cache |
| [Memcached](https://memcached.org/) | Official site |
