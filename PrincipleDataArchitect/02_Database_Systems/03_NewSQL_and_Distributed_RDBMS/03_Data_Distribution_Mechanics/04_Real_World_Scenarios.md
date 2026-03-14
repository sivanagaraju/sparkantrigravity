# Data Distribution Mechanics — FAANG War Stories & Real-World Scenarios

## Deployment Topology: Global Distribution at Scale

```mermaid
graph TD
    subgraph "Global Load Balancing Layer"
        DNS[Route53 / Global DNS]
        CDN[Cloudflare / Cloudfront]
    end
    
    subgraph "US-East (Virginia)"
        AppE[App Servers]
        DB_E1[(Shard 1 Primary)]
        DB_E2[(Shard 2 Replica)]
        DB_E3[(Shard 3 Replica)]
    end
    
    subgraph "EU-West (Ireland)"
        AppEU[App Servers]
        DB_EU1[(Shard 1 Replica)]
        DB_EU2[(Shard 2 Primary)]
        DB_EU3[(Shard 3 Replica)]
    end
    
    subgraph "AP-South (Mumbai)"
        AppAP[App Servers]
        DB_AP1[(Shard 1 Replica)]
        DB_AP2[(Shard 2 Replica)]
        DB_AP3[(Shard 3 Primary)]
    end

    DNS --> AppE
    DNS --> AppEU
    DNS --> AppAP
    
    AppE --> DB_E1
    AppEU --> DB_EU2
    AppAP --> DB_AP3
    
    DB_E1 -.->|Async Replication| DB_EU1
    DB_E1 -.->|Async Replication| DB_AP1
    
    note right of DB_E1: Geo-partitioning explicitly ties primary<br/>shard ownership to physical region.
```

## Case Study 1: Discord's Trillion-Message Migration (MongoDB to Cassandra to ScyllaDB)

Discord originally stored chats in MongoDB. As user counts exploded, the replica set primary became I/O constrained. They couldn't write fast enough to a single monolithic primary. 

*   **The Scale:** Billions of messages read/written per day.
*   **The Trap:** Sticking to single-leader topology (MongoDB replica sets) for a write-heavy, highly distributed workload.
*   **The Pivot:** They migrated to Apache Cassandra (Hash Partitioning). They chose the channel ID and message ID as a composite partition key. This allowed reads for a specific channel to hit exactly one node, avoiding scatter-gather.
*   **The Climax:** Sometime later, JVM garbage collection in Cassandra caused latency spikes. Discord eventually migrated from Cassandra to ScyllaDB (C++ rewrite of Cassandra) to bypass JVM GC pauses and extract maximum disk I/O, hitting sub-millisecond tail latencies.

## Case Study 2: Instagram's PostgreSQL Sharding

Instagram was able to scale to a billion users almost entirely on PostgreSQL before the NoSQL craze took over completely.

*   **The Scale:** Millions of photos uploaded, billions of likes per day.
*   **The Trap:** Putting all `user_data` in one massive DB instance until it literally hit AWS EBS volume limits.
*   **The Fix:** Application-level logical sharding. They built a custom ID generator using PL/pgSQL that embedded the logical shard ID inside a 64-bit ID.
    *   `41 bits` for time in milliseconds.
    *   `13 bits` for the logical shard ID (allowing 8,192 logical shards).
    *   `10 bits` for an auto-incrementing sequence.
*   **The Result:** The application extracts the 13 bits of the logical shard ID from the photo ID, looks up which physical Postgres instance currently hosts that logical shard in Zookeeper, and routes the query directly there.

## Case Study 3: GitHub's MySQL "Vitess" Migration

GitHub stored the metadata for every repo, issue, and pull request in massive monolithic MySQL clusters.

*   **The Scale:** Thousands of queries per second per database, approaching physical hardware ceilings for query concurrency.
*   **The Trap:** Vertical scaling hit a wall. Managing manual custom sharding logic in the Ruby on Rails monolithic application became too dangerous and slowed down product teams.
*   **The Fix:** Adoption of **Vitess** (originally developed at YouTube). Vitess acts as an intelligent proxy layer. To the application, it looks like one massive database. Under the hood, Vitess hashes the data, stores the topology in `etcd`, and routes queries to thousands of small, underlying MySQL instances.

## Incident Post-Mortem: The "Celebrity Account" Hotspot

**The Incident:** A social network experienced massive latency spikes and cascading timeouts affecting random users across the platform.
**Root Cause:** The database was range-partitioned by `User ID`. An extremely famous celebrity posted a viral image. Millions of users commented/liked simultaneously. All those writes targeted the specific database shard holding the celebrity's data. Since it was range-partitioned, that single physical node hit 100% CPU lock contention while the other 999 nodes in the cluster sat idle.
**The Fix:** 
1.  **Immediate:** Implement aggressive caching / write-coalescing in the application layer (Redis) before hitting the disk.
2.  **Structural:** Change the partition key for the highly-contended table (e.g., `likes`) to a hash of `(post_id + user_id)` instead of just `post_id`. This uniformly scatters the viral engagement writes across the entire cluster, breaking the bottleneck.
