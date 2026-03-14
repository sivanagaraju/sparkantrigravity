# Redis Cluster and Sentinel — Concept Overview

> Scaling Redis horizontally and ensuring high availability.

## Redis Cluster vs Sentinel

| Feature | Redis Sentinel | Redis Cluster |
|---|---|---|
| **Purpose** | High availability (failover) | Horizontal scaling + HA |
| **Sharding** | ❌ No (single master) | ✅ 16,384 hash slots |
| **Auto-failover** | ✅ Promotes replica | ✅ Promotes replica per shard |
| **Data Distribution** | All data on one master | Data split across N masters |
| **Max Data** | Limited by single node RAM | Sum of all node RAM |
| **Use When** | Single master < 50GB, need HA | Data > 50GB or need write scaling |

## Hash Slot Distribution

```
Redis Cluster: 16,384 hash slots
Node A: slots 0-5460
Node B: slots 5461-10922  
Node C: slots 10923-16383

Key "user:123" → CRC16("user:123") % 16384 = slot 7842 → Node B
Key "user:456" → CRC16("user:456") % 16384 = slot 2105 → Node A
```

## War Story: Discord — Redis Cluster for Message Cache

Discord runs Redis Cluster with 100+ nodes to cache messages for 200M+ monthly active users. Each shard handles ~10GB of message cache. When a node fails, Redis Cluster automatically promotes a replica within seconds, with zero application-level intervention.

## References

| Resource | Link |
|---|---|
| [Redis Cluster](https://redis.io/docs/management/scaling/) | Official docs |
| [Redis Sentinel](https://redis.io/docs/management/sentinel/) | HA documentation |
