# Real-World Scenarios: Redis Cluster & Sentinel

## 01: Twitter (X) — Massive Redis Cluster Scale-Out
- **Scale**: Twitter generates millions of tweets per hour, requiring trillions of cache reads per day. A typical tweet payload must be fanned out to the localized timelines of millions of followers in milliseconds.
- **Architecture Decision**: Twitter maintains one of the largest Redis Clusters in the world. They initially utilized **Twemproxy** (an open-source proxy layer they wrote to shard Redis before Redis Cluster existed). Later segments transitioned to native horizontally scaled Redis instances.
- **The Core Problem Solved**: The memory capacity of physical hardware. Even if you buy a server with 2TB of RAM, rebuilding a 2TB Redis AOF file off disk on reboot takes hours. By splitting that 2TB data footprint across 100 Redis Cluster master nodes (20GB each), they achieve two critical things: 
  1. Failovers/restarts take seconds instead of hours.
  2. The network bandwidth (NIC) load of retrieving heavy cached media objects is naturally partitioned across 100 physical network interfaces, preventing 100Gbps switch bottlenecks at the server rack level.

## 02: GitLab — The Sentinel Split-Brain Outage (2017)
- **The Incident**: In 2017, GitLab suffered an infamous database and caching outage. While primarily a PostgreSQL incident, they also battled severe caching misconfigurations.
- **Root Cause Analysis (Post-Mortem)**:
  - Engineers misconfigured their Sentinel Quorum. They had exactly 2 Sentinel nodes across 2 availability zones (Instead of 3 nodes).
  - A transient network partition dropped packets between the two zones. 
  - Sentinel A (isolated with the Master) saw the Master as healthy.
  - Sentinel B (isolated with the Replica) couldn't see the Master. Because quorum mathematically required 2 votes, Sentinel B could NOT promote the Replica. 
  - When the network healed, differing configurations and manual engineering panics caused massive downtime.
  - Furthermore, applications hard-coded a "Wait for Redis" loop synchronously in production. When Sentinel failed to provide a Master IP temporarily, the Ruby on Rails application threads saturated instantaneously causing the global web farm to 502 Bad Gateway.
- **The Fix**: 
  1. Mandatory deployment of strictly odd numbers of Sentinel nodes (minimum 3) physically dispersed across 3 independent availability zones to satisfy the CAP theorem constraints.
  2. Rewrote frontend Ruby application loops to degrade gracefully. If Sentinel cannot return a Master IP within 2 seconds, the application ignores caching completely and serves degraded database throughput rather than taking down the website.

## 03: E-Commerce Flash Sale (Hash Slot Imbalance)
- **Scale**: A massive ticketing website opening Taylor Swift concert tickets at exactly 10:00:00 AM. Traffic rockets from 10k req/sec to 1.5M req/sec.
- **The Incident**: The e-commerce site deployed a 20-node Redis Cluster to cache the inventory count. At 10:00:01 AM, one specific Redis Master node hit 100% CPU utilization and crashed, while the other 19 Master nodes sat entirely idle at 2% CPU.
- **Root Cause Analysis**: The engineering team attempted to use a Hash Tag to lock the entire concert's inventory structure to avoid cross-slot transaction errors.
  - Key: `inventory:{TSWIFT2024}:vip` (Slot 114)
  - Key: `inventory:{TSWIFT2024}:ga` (Slot 114)
  - Key: `inventory:{TSWIFT2024}:log` (Slot 114)
  Every single one of the 1.5 million requests asking for ticket counts included the `{TSWIFT2024}` hash tag. The CRC16 algorithm routed exactly 1.5 million requests exclusively to Hash Slot 114. The Master node owning Slot 114 melted down within 1 second.
- **The Fix**: The team removed the Hash Tags. They deliberately distributed the VIP, GA, and Log counters across completely un-tagged random keys, allowing the CRC16 mathematical distribution to perfectly stripe the keys across the 20 Master nodes. They accepted the penalty of giving up atomic multi-key Lua scripts in favor of achieving perfect horizontal hardware saturation.

## Network Topology of the 6-Node Ideal Cluster

```mermaid
graph TD
    classDef main fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;
    classDef rep fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff;

    subgraph "Availability Zone A"
        M1[Master 1\n(Slots 0-5k)]:::main
        R3[Replica 3\n(Backs up M3)]:::rep
    end
    
    subgraph "Availability Zone B"
        M2[Master 2\n(Slots 5k-10k)]:::main
        R1[Replica 1\n(Backs up M1)]:::rep
    end
    
    subgraph "Availability Zone C"
        M3[Master 3\n(Slots 10k-16k)]:::main
        R2[Replica 2\n(Backs up M2)]:::rep
    end

    M1 -.->|Continuous Replication (Cross-AZ)| R1
    M2 -.->|Continuous Replication (Cross-AZ)| R2
    M3 -.->|Continuous Replication (Cross-AZ)| R3
```
*Note the explicit anti-affinity. Replicas are deliberately placed in physical data centers opposite to their Masters. If Availability Zone A suffers a total power loss, you lose Master 1 and Replica 3. Master 1's backup (Replica 1) is safely alive in Zone B, and Master 3 (which Replica 3 was backing up) is safely alive in Zone C. The cluster autonomously heals and promotes Replica 1 to Master, preventing any data loss.*
