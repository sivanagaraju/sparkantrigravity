# B-Trees vs LSM-Trees — Further Reading

---

## Papers

| Title | Authors | Link |
|---|---|---|
| The Log-Structured Merge-Tree (LSM-Tree) | O'Neil, Cheng, Gawlick, O'Neil (1996) | [cs.umb.edu/~poneil/lsmtree.pdf](https://www.cs.umb.edu/~poneil/lsmtree.pdf) |
| Organization and Maintenance of Large Ordered Indexes | Bayer & McCreight (1970) | [Original B-Tree paper — Acta Informatica] |
| WiscKey: Separating Keys from Values in SSD-Conscious Storage | Lu et al. (FAST 2016) | [usenix.org/conference/fast16/technical-sessions/presentation/lu](https://www.usenix.org/conference/fast16/technical-sessions/presentation/lu) |
| Dostoevsky: Better Space-Time Trade-Offs for LSM-Tree Based Key-Value Stores | Dayan & Idreos (SIGMOD 2018) | [dl.acm.org/doi/10.1145/3183713.3196930](https://dl.acm.org/doi/10.1145/3183713.3196930) |
| Gorilla: A Fast, Scalable, In-Memory Time Series Database | Pelkonen et al. (VLDB 2015) | [vldb.org/pvldb/vol8/p1816-teller.pdf](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf) |

## Books

| Title | Author | Relevant Chapters |
|---|---|---|
| *Designing Data-Intensive Applications* | Martin Kleppmann | Ch. 3: Storage and Retrieval (B-Trees, SSTables, LSM-Trees) |
| *Database Internals* | Alex Petrov | Ch. 1-7: Storage engine anatomy, B-Trees, LSM-Trees |
| *PostgreSQL 14 Internals* | Egor Rogov | Ch. 4-6: Page Layout, Buffer Manager, Indexing |

## Engineering Blogs

| Title | Source | Link |
|---|---|---|
| RocksDB Overview | Facebook Engineering | [github.com/facebook/rocksdb/wiki/RocksDB-Overview](https://github.com/facebook/rocksdb/wiki/RocksDB-Overview) |
| Under the Hood: Building and Open-Sourcing RocksDB | Facebook Engineering | [engineering.fb.com/2013/11/21/core-infra/under-the-hood-building-and-open-sourcing-rocksdb/](https://engineering.fb.com/2013/11/21/core-infra/under-the-hood-building-and-open-sourcing-rocksdb/) |
| Compaction Analysis | Cockroach Labs | [cockroachlabs.com/blog/pebble-lsm-compaction](https://www.cockroachlabs.com/blog/) |
| How We Halved Go Monorepo CI Build Time | Uber Engineering | [uber.com/blog/how-we-halved-go-monorepo-ci-build-time](https://www.uber.com/blog/) |

## Conference Talks

| Title | Speaker | Event |
|---|---|---|
| The LSM-Tree and the B-Tree: Similarities, Differences, and Trade-offs | Alex Petrov | Strange Loop 2018 |
| RocksDB Performance and Tuning | Siying Dong | Percona Live 2019 |
| PostgreSQL Internals Through Pictures | Bruce Momjian | PGConf 2020 |

## GitHub Repos

| Repo | Description |
|---|---|
| [facebook/rocksdb](https://github.com/facebook/rocksdb) | LSM-based key-value store by Facebook |
| [cockroachdb/pebble](https://github.com/cockroachdb/pebble) | Go LSM-based engine (RocksDB-inspired) by Cockroach Labs |
| [google/leveldb](https://github.com/google/leveldb) | Original LSM key-value store by Jeff Dean and Sanjay Ghemawat |
| [postgres/postgres](https://github.com/postgres/postgres) | PostgreSQL source code (B-Tree in `src/backend/access/nbtree/`) |
| [awesome-database-learning](https://github.com/pingcap/awesome-database-learning) | Curated database internals resources by PingCAP |

## Official Documentation

| Topic | Link |
|---|---|
| PostgreSQL B-Tree Index | [postgresql.org/docs/current/btree.html](https://www.postgresql.org/docs/current/btree.html) |
| PostgreSQL Page Layout | [postgresql.org/docs/current/storage-page-layout.html](https://www.postgresql.org/docs/current/storage-page-layout.html) |
| RocksDB Tuning Guide | [github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide) |
| RocksDB Bloom Filter | [github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter](https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter) |

## Cross-References

| Topic | Path |
|---|---|
| Page Architecture | [../02_Page_Architecture](../02_Page_Architecture/) |
| Compaction Strategies | [../03_Compaction_Strategies](../03_Compaction_Strategies/) |
| MVCC Internals | [../../02_Transactions_and_Consistency/01_MVCC_Internals](../../02_Transactions_and_Consistency/01_MVCC_Internals/) |
| NewSQL (RocksDB underpins CockroachDB/TiDB) | [../../03_NewSQL_and_Distributed_RDBMS/01_Spanner_Cockroach_TiDB](../../03_NewSQL_and_Distributed_RDBMS/01_Spanner_Cockroach_TiDB/) |
