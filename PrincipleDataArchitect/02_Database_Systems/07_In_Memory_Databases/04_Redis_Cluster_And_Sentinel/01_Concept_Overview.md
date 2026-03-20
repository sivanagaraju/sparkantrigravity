# Concept Overview: Redis Sentinel & Redis Cluster

## Why This Exists
A single Redis instance is blindingly fast but represents a terrifying Single Point of Failure (SPOF). If the node crashes, the entire cache is gone, exposing the backend database to immediate destruction. Furthermore, a single Redis process is strictly constrained to 1 CPU core and the physical RAM of one machine. 
To solve the **Availability** problem, Redis introduced **Sentinel** (Active-Passive failover). 
To solve the **Scalability** problem, Redis introduced **Redis Cluster** (Active-Active horizontal sharding). 

## What Value It Provides

| Benefit | Quantified Impact |
|---|---|
| **High Availability (HA)** | Sentinel automatically promotes a Replica to Primary in **< 3 seconds** during a crash, allowing client libraries to reconnect seamlessly without human intervention. |
| **Horizontal Scaling (Sharding)** | Redis Cluster distributes the data across up to **1,000 nodes**, pushing total cache capacity from 256GB (one machine) to hundreds of Terabytes. |
| **Throughput Expansion** | Because Redis is single-threaded, a 6-node Redis Cluster provides exactly **6x the CPU cycles** for query processing compared to a standalone node. |
| **Split-Brain Prevention** | Both systems utilize distributed consensus (Quorum/Epochs) to ensure network partitions don't accidentally create two fighting "Master" nodes that irreversibly corrupt data. |

## Where It Fits

```mermaid
graph TD
    classDef client fill:#2d3436,stroke:#b2bec3,stroke-width:2px,color:#dfe6e9;
    classDef main fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;
    classDef rep fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff;
    classDef sent fill:#e17055,stroke:#fab1a0,stroke-width:2px,color:#fff;

    subgraph "Option A: Redis Sentinel (HA Only)"
        SApp[App Tier]:::client
        Sent1[Sentinel 1]:::sent
        Sent2[Sentinel 2]:::sent
        Sent3[Sentinel 3]:::sent
        MainA[Primary (Master)]:::main
        RepA[Replica (Slave)]:::rep
        RepB[Replica (Slave)]:::rep
        
        Sent1 -.- Sent2 -.- Sent3
        Sent1 -.->|Pings/Monitors| MainA
        MainA == "Async Replication" ==> RepA
        MainA == "Async Replication" ==> RepB
        SApp -->|Queries current Primary from Sentinel| MainA
    end

    subgraph "Option B: Redis Cluster (HA + Sharding)"
        CApp[App Tier: 'Smart' Client]:::client
        M1[Master A\nSlots 0-5460]:::main
        M2[Master B\nSlots 5461-10922]:::main
        M3[Master C\nSlots 10923-16383]:::main
        R1[Replica A]:::rep
        R2[Replica B]:::rep
        R3[Replica C]:::rep
        
        M1 == Repl ==> R1
        M2 == Repl ==> R2
        M3 == Repl ==> R3
        
        M1 -.-|Gossip Protocol| M2 -.-|Gossip| M3
        
        CApp -->|Hash mod 16384| M2
    end
```

## When To Use / When NOT To Use

| Scenario | Verdict | Why / Alternative |
|---|---|---|
| Need HA for a 50GB cache, but total queries < 100k ops/sec | ✅ **SENTINEL** | Simple, easy to reason about. Client libraries are ubiquitous. No cross-slot transaction restrictions. |
| Need a 2 Terabyte cache pushing 5 Million ops/sec | ✅ **CLUSTER** | Mandatory. A single master physically cannot hold 2TB of RAM or execute 5M ops/sec on one core. |
| Using complex multi-key Lua scripts or `mget/mset` over massive data | ❌ **CLUSTER** | Redis Cluster strictly bans operations spanning multiple keys *unless* the keys explicitly hash to the exact same cluster Slot (Hash Tags `{}`). Cluster breaks native transactional semantics. |
| You just want simple multi-processing on one 64-core box | ❌ **BOTH** | Running Cluster locally just to use 64 cores is painful. Use **Memcached**, which is natively horizontally threaded. |

## Key Terminology

| Term | Definition & Operational Significance |
|---|---|
| **Quorum** | The minimum number of Sentinel nodes (e.g., 2 out of 3) that must physically agree the Master is dead before initiating a failover. Prevents Split-Brain. |
| **Epoch** | A monotonically increasing integer representing the current "generation" of the cluster layout. If Sentinel A issues failover commands on Epoch 5, and Sentinel C issues on Epoch 6, the cluster universally respects Epoch 6. |
| **Hash Slot** | Redis Cluster divides the universe of all possible keys into exactly **16,384** Hash Slots. (`CRC16(key) mod 16384`). |
| **MOVED Redirection** | If a naive client asks Master A for a key that actually lives on Master C, Master A responds with a hard error: `MOVED 11043 192.168.1.5:6379`. The client must reconnect to node C. |
| **Gossip Protocol** | How nodes in a Cluster discover cluster state. They continuously ping each other to share metadata about who holds which Hash Slots and which nodes are unresponsive. |
| **Split-Brain** | When a network cable breaks the datacenter in half. Subnet A thinks the Master is dead and promotes a Replica to Master. Subnet B keeps the old Master. Now you have TWO Masters accepting independent, diverging writes that can never be reconciled. |
