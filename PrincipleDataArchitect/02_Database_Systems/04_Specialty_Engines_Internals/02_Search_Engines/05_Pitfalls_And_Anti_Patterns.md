# Pitfalls & Anti-Patterns: Search Engines

## 1. The Dynamic Mapping Explosion

Search engines attempt to be helpful by automatically inferring schemas (mappings) from incoming JSON. If unstructured or maliciously crafted JSON is indexed, the engines create a new column/field definition in the cluster state for every new JSON key.

*   **Symptom**: Master node crashes, cluster state updates take seconds, `IllegalArgumentException: Limit of mapping fields [10000] has been exceeded`.
*   **Detection**: Audit `GET /_cluster/state` and observe massive mapping payloads.
*   **Fix**: Set `"dynamic": "strict"` or `"dynamic": "runtime"` at the index mapping level. Restructure nested, dynamic key-value pairs into explicit lists of objects (`[{"key": "a", "value": 1}]`).

## 2. Deep Pagination (Iterating via `from`/`size`)

Fetching page 1,000 of a search result by passing `from: 10000, size: 10` forces the coordinating node to request the top 10,010 results from *every* shard, sort them all in RAM, and discard 10,000 of them.

*   **Symptom**: High heap usage on coordinating nodes, queries timing out on deeper pages.
*   **Detection**: Monitor the Slow Log for queries with high `from` parameters.
*   **Fix**: Use the `search_after` parameter with a reliable tie-breaker (like `_id`) to cursor through results without deep sorting, or use the Point in Time (PIT) API.

## 3. Oversharding (Too Many Small Shards)

Every shard in Lucene is a complete engine with its own memory overhead, file handles, and thread pools. If you create an index per day (for logs) with 5 shards each, after a year you have 1,825 indices and 9,125 shards holding tiny amounts of data.

*   **Symptom**: A cluster with terabytes of RAM crashing under the weight of 500GB of actual data. High baseline CPU usage, long recovery times.
*   **Detection**: `GET /_cat/shards` reveals thousands of shards under 1GB in size.
*   **Fix**: Aim for shard sizes between **20GB and 50GB**. Use Index Lifecycle Management (ILM) Rollover to automatically create a new index only when the current one reaches 50GB, rather than strictly by time.

## 4. Treating Search Engines as a Primary DB (System of Record)

Attempting to write transactional data to Elasticsearch as the authoritative source.

*   **Symptom**: Data loss during network partitions. Inability to execute complex relational JOINs. Severe write contention.
*   **Detection**: Architecture reviews showing ES as the sole storage tier for user accounts or ledger balances.
*   **Fix**: Elasticsearch is a *projection*. Keep authoritative data in Postgres/DynamoDB and replicate to ES via CDC (Change Data Capture) or Dual-Write patterns.

## Decision Matrix: When is Search the WRONG Choice?

| Scenario | Why Search Fails | Choose Instead |
|---|---|---|
| **High Write Frequency** | Segments must be merged, generating massive I/O amplification for constant point-updates. | ScyllaDB, Cassandra, DynamoDB |
| **Strict ACID Guarantees** | Distributed search prioritizes Availability and Partition Tolerance. Historically struggles with split brain and dirty reads. | PostgreSQL, CockroachDB |
| **Deep Analytic Joins** | Denormalization is required. ES has no efficient equivalent to a SQL hash join across millions of rows at runtime. | Snowflake, BigQuery, ClickHouse |
| **Graph Traversals** | Cannot efficiently navigate relationships of unknown depth (e.g., Friends of Friends of Friends). | Neo4j, Neptune |
