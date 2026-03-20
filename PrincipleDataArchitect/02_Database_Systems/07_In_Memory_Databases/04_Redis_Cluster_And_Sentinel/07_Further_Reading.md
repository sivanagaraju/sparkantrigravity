# Further Reading: Redis Sentinel & Cluster

## 📚 Books
- **Redis in Action** by Josiah L. Carlson (ISBN: 9781617290855) — *Chapter 10 provides a deep dive into replicating Redis and setting up automated failovers manually, outlining the exact mechanisms Sentinel automated.*
- **Designing Data-Intensive Applications** by Martin Kleppmann (ISBN: 9781449373320) — *Read Chapter 5 (Replication) to fundamentally understand the physics of Split-Brain and Multi-Leader topologies which affect Sentinel configurations.*

## 📄 Core Specifications & Jepsen Analysis
- **[The Redis Cluster Specification](https://redis.io/docs/reference/cluster-spec/)** (Salvatore Sanfilippo) — *The authoritative foundational document. Explains CRC16 Hash Slots, the Gossip protocol, Configuration Epochs, and cross-slot blocking physics.*
- **[Jepsen: Redis Sentinel](https://jepsen.io/analyses/redis-sentinel)** (Kyle Kingsbury) — *A legendary, brutal distributed systems test. Proves that Redis Sentinel is explicitly NOT a CP (Consistent) system. Documents exactly how write-loss occurs during network partitions before the `min-replicas-to-write` configuration was standardized.*
- **[Jepsen: Redis Raft](https://jepsen.io/analyses/redis-raft-1b3f66c)** (Kyle Kingsbury) — *Analyzing the eventual push to make Redis strictly consistent via Raft modules.*

## 🏢 Enterprise Engineering Blogs
- **[Scaling Redis at Twitter](https://blog.twitter.com/engineering/en_us/topics/infrastructure/2019/the-architecture-of-twitters-new-caching-service)** (Twitter Engineering) — *Details their migration from Twemproxy to fully sharded cluster infrastructure.*
- **[Discord: How we scaled to 5 million concurrent users](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users)** (Discord Engineering) — *Discussion around Pub/Sub routing using Elixir and massive horizontally sharded Redis nodes for websocket routing arrays.*
- **[Scaling Redis at GitHub](https://github.blog/2019-10-18-scaling-git-ssh-at-github/)** (GitHub Engineering) — *How GitHub uses Redis for high-availability access control rate-limiting across their globe-spanning fleet.*

## 📺 Conference Talks
- **[Redis Cluster: Under the Hood](https://www.youtube.com/watch?v=3_f_dI1t9B4)** (RedisConf) — *Visualized packet journeys of how nodes execute Gossip protocols using the Cluster Bus (port 16379) to detect dead masters.*
- **[Failover at Scale with Redis Sentinel](https://www.youtube.com/watch?v=R9_uQJ8k658)** — *Analyzing the latency blip during the 3-second failover window, and how Java/Python client architectures must retry requests to survive the drop natively.*

## 💻 Curated GitHub Repositories & Docs
- **[redis/redis/src/cluster.c](https://github.com/redis/redis/blob/unstable/src/cluster.c)** — *The actual C implementation of the Gossip Protocol. Search for `clusterSendPing` to see how node status is broadcasted over the wire.*
- **[Grokking Redis Cluster Smart Clients](https://github.com/Grokzen/redis-py-cluster)** — *The codebase for the Python cluster driver. Look at the `NodeManager` class to see exactly how the client caches the 16,384 Hash Slot map in RAM.*

## 🔗 Cross-References within this Curriculum
- For details on the internal data structures that live inside these slots, read `01_Redis_Data_Structures`.
- For background on alternative horizontal scaling topologies (Multi-threaded Shared-Nothing), refer to `02_Memcached`.
