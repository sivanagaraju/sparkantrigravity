# Compaction Strategies — Further Reading

---

## Papers

| Title | Authors | Link |
|---|---|---|
| The Log-Structured Merge-Tree (LSM-Tree) | O'Neil et al. (1996) | [cs.umb.edu/~poneil/lsmtree.pdf](https://www.cs.umb.edu/~poneil/lsmtree.pdf) |
| WiscKey: Separating Keys from Values in SSD-conscious Storage | Lu et al. (FAST 2016) | [usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf](https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf) |
| Monkey: Optimal Navigable Key-Value Store | Dayan et al. (SIGMOD 2017) | [stratos.seas.harvard.edu/files/stratos/files/monkey.pdf](http://stratos.seas.harvard.edu/files/stratos/files/monkey.pdf) |
| Dostoevsky: Better Space-Time Trade-Offs for LSM-Tree Based Key-Value Stores via Adaptive Removal of Superfluous Merging | Dayan et al. (SIGMOD 2018) | [stratos.seas.harvard.edu/files/stratos/files/dostoevsky.pdf](http://stratos.seas.harvard.edu/files/stratos/files/dostoevsky.pdf) |

## Books

| Title | Author | Relevant Chapters |
|---|---|---|
| *Database Internals* | Alex Petrov | Ch. 7: Log-Structured Storage (in-depth breakdown of Compaction) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | Ch. 3: Storage and Retrieval (SSTables and LSM-Trees) |
| *Cassandra: The Definitive Guide* | Jeff Carpenter, Eben Hewitt | Ch. 9: Reading and Writing Data (Compaction Strategies) |

## Engineering Blogs

| Title | Source | Link |
|---|---|---|
| Under the Hood: Compaction | RocksDB Wiki | [github.com/facebook/rocksdb/wiki/Compaction](https://github.com/facebook/rocksdb/wiki/Compaction) |
| Leveled Compaction in Cassandra | DataStax Blog | [datastax.com/blog/leveled-compaction-in-apache-cassandra](https://www.datastax.com/blog/leveled-compaction-in-apache-cassandra) |
| Time Window Compaction Strategy (TWCS) | ScyllaDB Blog | [scylladb.com/2016/12/28/time-window-compaction-strategy](https://www.scylladb.com/2016/12/28/time-window-compaction-strategy/) |
| How We Reduced Write Amplification by 90% | Cloudflare | [blog.cloudflare.com/how-we-scaled-nginx-and-saved-the-world-54-years-every-day/](https://blog.cloudflare.com/) (Discusses LSM write volume optimization) |

## Tools & Frameworks

| Tool | Purpose | Link |
|---|---|---|
| `nodetool compactionstats` | CLI to monitor active compactions in Cassandra/ScyllaDB | [cassandra.apache.org/doc/latest/cassandra/tools/nodetool/compactionstats.html](https://cassandra.apache.org/doc/latest/cassandra/tools/nodetool/compactionstats.html) |
| RocksDB `db_bench` | Benchmark tool to simulate workloads and measure Write Amplification | [github.com/facebook/rocksdb/wiki/Benchmarking-tools](https://github.com/facebook/rocksdb/wiki/Benchmarking-tools) |
| `sstableutil` | Apache Cassandra tool to list and inspect SSTable files | [cassandra.apache.org/doc/latest/cassandra/tools/sstable/sstableutil.html](https://cassandra.apache.org/doc/latest/cassandra/tools/sstable/sstableutil.html) |

## Cross-References

| Topic | Path |
|---|---|
| B-Trees vs LSM-Trees | [../01_B_Trees_vs_LSM_Trees](../01_B_Trees_vs_LSM_Trees/) |
| Page Architecture | [../02_Page_Architecture](../02_Page_Architecture/) |
| Wide-Column Stores (Cassandra) | [../../04_Specialty_Engines_Internals/06_Wide_Column_Stores](../../04_Specialty_Engines_Internals/06_Wide_Column_Stores/) |
| Apache Kafka Internals (Log compaction) | [../../../04_Streaming_and_Event_Driven/02_Message_Brokers/01_Kafka_Architecture](../../../04_Streaming_and_Event_Driven/02_Message_Brokers/01_Kafka_Architecture/) |
