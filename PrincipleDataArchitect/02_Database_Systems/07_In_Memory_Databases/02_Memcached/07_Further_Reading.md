# Further Reading: Memcached 

## 📚 Books
- **Designing Data-Intensive Applications** by Martin Kleppmann (ISBN: 9781449373320) — *Provides fundamental insights into distributed caching logic and consistent hashing implementation.*
- **High Performance MySQL** by Baron Schwartz, Peter Zaitsev, Vadim Tkachenko (ISBN: 9781449314286) — *Chapter 12 details specifically how scaling MySQL is effectively impossible without a massive secondary read-aside Memcached architectural layer.*

## 📄 Academic Papers & Core Articles
- **[Scaling Memcache at Facebook](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf)** (Rajesh Nishtala et al., NSDI 2013) — *Required reading. The definitive paper on operating caching infrastructure at multi-petabyte scale. Details UDP bridging, lease mechanisms, and connection pooling.*
- **[Optimal Probabilistic Cache Stampede Prevention](https://en.wikipedia.org/wiki/Cache_stampede)** (Vattani et al., VLDB 2015) — *The original mathematical proof for XFetch / Probabilistic Early Expiration (the $now - delta * beta * (-ln(rand)) > expiry$ formula).*
- **[Replacing the Memcached LRU](https://memcached.org/blog/modern-lru/)** (Dormando, 2018) — *The core developer of Memcached detailing why the standard LRU was broken by background scans, and how the HOT/WARM/COLD segmented LRU fixed it.*

## 🏢 FAANG Engineering Blogs
- **[Facebook’s Mcrouter Architecture](https://engineering.fb.com/2014/09/15/web/introducing-mcrouter-a-memcached-protocol-router-for-scaling-memcached-deployments/)** (Facebook Engineering) — *Detailed breakdown of the open-source proxy layer resolving TCP connection flooding issues.*
- **[EVCache: Netflix's distributed in-memory datastore](https://netflixtechblog.com/evcache-the-tale-of-a-distributed-in-memory-datastore-456673bc2888)** (Netflix Tech Blog) — *Why Netflix chose Memcached over Redis for massive global user presence clustering.*
- **[A Memcached crash course via GitHub](https://github.blog/2018-03-01-ddos-incident-report/)** (GitHub Engineering) — *The dramatic incident report of the 1.35 Terabit globally coordinated Memcached UDP Amplification DDoS attack.*

## 📺 Conference Talks
- **[Extstore: Expanding Memcached with NVMe Flash](https://www.youtube.com/watch?v=FjI1E2P50-g)** (Dormando @ USENIX) — *A phenomenal deep dive into C internals on how Memcached moved values to Flash Drives while keeping pointers in RAM to scale caches infinitely without buying terabytes of DDR4.*

## 💻 Curated GitHub Repositories & Docs
- **[memcached/memcached (Source Code)](https://github.com/memcached/memcached)** — *Review `slabs.c` for the memory allocator logic, and `items.c` for the LRU mechanism.*
- **[facebook/mcrouter](https://github.com/facebook/mcrouter)** — *The C++ connection pooling router built at Facebook.*
- **[Official Extstore Documentation](https://github.com/memcached/memcached/wiki/Extstore)** — *The authoritative guide to configuring Extstore for massive cold-caching.*

## 🔗 Cross-References within this Curriculum
- For details on bypassing transient caches with pure single-threaded complex structures, see `01_Redis_Data_Structures`.
- Read how cache misses hit the database layer physically in `01_Storage_Engines_and_Disk_Layout`.
