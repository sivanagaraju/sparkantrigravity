# Further Reading: Redis Data Structures

## 📚 Books
- **Redis in Action** by Josiah L. Carlson (ISBN: 9781617290855) — *Chapter 9 covers reducing memory usage with short structures (Ziplists/Listpacks).*
- **Data Intensive Applications** by Martin Kleppmann (ISBN: 9781449373320) — *Chapter 3 covers B-Trees vs LSM Trees vs In-Memory representations (Skiplists).*
- **System Design Interview (Volume 2)** by Alex Xu (ISBN: 9781736049112) — *Proximity caching and real-time gaming leaderboard system design utilizing Redis ZSets.*

## 📄 Academic Papers & Core Articles
- **[Skip Lists: A Probabilistic Alternative to Balanced Trees](https://epubs.siam.org/doi/abs/10.1137/0219022)** (William Pugh, 1990) — *The foundational math behind why Redis `ZSET` doesn't use standard Red-Black Trees.*
- **[Redis under the hood](https://pauladamsmith.com/articles/redis-under-the-hood.html)** (Paul Adam Smith) — *Detailed breakdown of the `dict.c` and `sds.c` C implementations.*
- **[A tale of two allocators: jemalloc vs glibc](https://engineering.linkedin.com/blog/2021/a-tale-of-two-allocators)** (LinkedIn Engineering) — *Why systems like Redis rely on `jemalloc` to prevent severe memory fragmentation.*

## 🏢 FAANG Engineering Blogs
- **[How X (Twitter) Caches the Timeline at Scale](https://blog.twitter.com/engineering/en_us.html)** (Twitter Engineering) — *Detailing their fan-out-on-write Lists implementation and hybrid pull mechanism for massive accounts.*
- **[Scaling Redis at Twitter](https://blog.twitter.com/engineering/en_us/topics/infrastructure/2019/scaling-redis-at-twitter.html)** (Twitter Engineering) — *Moving from hundreds of instances to massive clustered orchestration.*
- **[Discord: How we scaled to 5 million concurrent users](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users)** (Discord Engineering) — *Using Redis for fast, volatile state management in presence tracking.*

## 📺 Conference Talks
- **[Keynote: The state of Redis](https://www.youtube.com/watch?v=kRkaH-EvbMw)** (Salvatore Sanfilippo) — *The creator of Redis explains design philosophy, why it remained single-threaded, and future C improvements.*
- **[Redis at 1,000,000 Requests per Second](https://www.youtube.com/watch?v=LcwE6F0o16w)** (RedisConf) — *Demonstrating pipelining, multi-key operations, and OS-level Unix socket tuning to bypass TCP limits.*

## 💻 Curated GitHub Repositories & Docs
- **[redis/redis (Source Code)](https://github.com/redis/redis/tree/unstable/src)** — *Read `dict.c`, `sds.c`, and `t_zset.c`. They are exceptionally well-commented C code.*
- **[DragonflyDB](https://github.com/dragonflydb/dragonfly)** — *A modern, multi-threaded C++ drop-in replacement for Redis. Reading their docs helps understand Redis's architectural limitations.*
- **[Official Memory Optimization Guide](https://redis.io/docs/management/optimization/memory-optimization/)** — *Critical docs on adjusting `hash-max-listpack-entries` to compress RAM usage.*

## 🔗 Cross-References within this Curriculum
- For details on how Redis replicates these data structures asynchronously, see `04_Redis_Cluster_And_Sentinel`.
- For a comparison with a purely transient cache with a multi-threaded architecture, see `02_Memcached`.
