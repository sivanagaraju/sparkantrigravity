# Property Graphs — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Using a Graph Database for Tabular/OLAP Workloads

**The mistake**: Storing transactional data (orders, invoices, line items) in a graph database and trying to run aggregation queries.

```cypher
// ❌ WRONG: Aggregation query in Neo4j
// "Total revenue by product category this quarter"
MATCH (o:Order)-[:CONTAINS]->(li:LineItem)-[:IS_PRODUCT]->(p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE o.order_date >= date('2024-01-01')
RETURN c.name, SUM(li.quantity * li.unit_price) AS revenue
ORDER BY revenue DESC;
// Requires full graph traversal through 4 labels
// No columnar storage, no predicate pushdown, no partition pruning
// Neo4j: 45 seconds. PostgreSQL: 2 seconds.
```

**What breaks**: Graph databases are optimized for traversal (following edges), not aggregation (scanning and summing columns). They lack columnar storage, vectorized execution, and partition pruning — the features that make OLAP databases fast.

**Detection**:

- Profile Cypher queries. If >50% of queries are `RETURN ... SUM/COUNT/AVG ... GROUP BY`, you're using the wrong tool
- Check query execution plans for full-label scans (`NodeByLabelScan`) on aggregation queries

**Fix**: Use a relational/columnar database for OLAP. Use the graph for traversal-heavy queries. Feed graph-derived features (PageRank, centrality) back into the relational warehouse as columns.

---

## Anti-Pattern 2: No Indexes on Lookup Properties

**The mistake**: Querying by property values without creating indexes. Every query becomes a full label scan.

```cypher
// ❌ WRONG: No index on Person.email
MATCH (p:Person {email: 'alice@example.com'})-[:KNOWS]->(friend)
RETURN friend.name;
// Without index: scans ALL Person nodes to find email match
// With 100M Person nodes: 30 seconds
// With index: <5ms
```

**Detection**:

- Run `EXPLAIN` on queries. Look for `NodeByLabelScan` instead of `NodeIndexSeek`
- Check existing indexes: `SHOW INDEXES` in Neo4j
- Monitor: slow query log for queries >1s

**Fix**:

```cypher
// ✅ Create indexes on properties used in WHERE/MATCH predicates
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.person_id IS UNIQUE;
// Now the same query uses NodeIndexSeek: <5ms
```

---

## Anti-Pattern 3: Unbounded Traversals (No Depth Limit)

**The mistake**: Writing traversal queries without limiting the path depth.

```cypher
// ❌ WRONG: Unbounded variable-length path
MATCH path = (a:Person)-[:KNOWS*]->(b:Person)
WHERE a.name = 'Alice' AND b.name = 'Zara'
RETURN path;
// This explores EVERY possible path of ANY length
// In a connected graph of 1M nodes, this is effectively infinite
// Query will never complete or OOM the database
```

**What breaks**: Unbounded traversals in a connected graph explore exponentially growing paths. O(k^d) where k = average degree and d = depth. With k=150 and no limit, depth 6 = 150^6 = 11 trillion paths.

**Detection**:

- Search Cypher queries for `[:TYPE*]` without bounds (should be `[:TYPE*..6]`)
- Monitor: queries consuming >80% of heap memory
- Check for OOM errors in Neo4j logs

**Fix**: Always bound traversals:

```cypher
// ✅ BOUNDED: Max 6 hops
MATCH path = shortestPath(
    (a:Person {name: 'Alice'})-[:KNOWS*..6]-(b:Person {name: 'Zara'})
)
RETURN path;
// Uses BFS with depth limit. Deterministic runtime.
```

---

## Anti-Pattern 4: Modeling Everything as Nodes (Missing Edge Properties)

**The mistake**: Creating intermediate nodes for what should be edge properties.

```cypher
// ❌ WRONG: Employment as an intermediate node
// Person -[:HAS_EMPLOYMENT]-> Employment -[:AT_COMPANY]-> Company
// Employment has: role, start_date, department
// This creates 2x the edges and an unnecessary node

CREATE (e:Employment {role: 'Engineer', start_date: date('2020-01-01')})
CREATE (p)-[:HAS_EMPLOYMENT]->(e)
CREATE (e)-[:AT_COMPANY]->(c)
// 3 entities, 2 edges — for a simple "Alice works at Acme as Engineer"
```

**What breaks**: Every relationship traversal now requires 2 hops instead of 1. Queries become more complex, slower, and harder to read.

**Fix**: Use edge properties:

```cypher
// ✅ CORRECT: Employment as edge properties
CREATE (p)-[:WORKS_AT {role: 'Engineer', since: date('2020-01-01'), dept: 'Platform'}]->(c)
// 2 entities, 1 edge. Simple. Fast. Readable.
```

**Exception**: If the "employment" itself has relationships (e.g., employment → performance_review, employment → salary_band), then the intermediate node is justified. This is called **reification** — turning a relationship into a node when it needs its own relationships.

---

## Anti-Pattern 5: Not Monitoring Super Nodes

**The mistake**: Allowing high-degree nodes (super nodes) to grow unchecked until they cause cascading timeouts.

**Detection**:

```cypher
// Find super nodes — nodes with >10K edges
MATCH (n)-[r]-()
WITH n, COUNT(r) AS degree
WHERE degree > 10000
RETURN labels(n), n.name, degree
ORDER BY degree DESC;
```

**Fix**:

1. **Alert**: Set up monitoring for node degree >100K
2. **Pre-compute**: Cache results for super node traversals
3. **Partition**: Split super node edges into typed sub-groups
4. **Limit**: Use `LIMIT` in intermediate traversals to cap expansion

---

## Decision Matrix — When Property Graphs Are the WRONG Choice

| Scenario | Why Graphs Are Wrong | Better Alternative |
|---|---|---|
| OLAP aggregation (SUM, AVG, GROUP BY) | No columnar storage, no vectorized execution | PostgreSQL, Snowflake, BigQuery |
| High-volume OLTP (10K+ writes/sec) | Graph databases have lower write throughput than RDBMS | PostgreSQL, MySQL |
| Simple key-value lookups | Graph overhead for non-relational data | Redis, DynamoDB |
| Time-series data (metrics, IoT) | Temporal queries not native to graph model | TimescaleDB, InfluxDB |
| Document storage (nested JSON) | Graphs add edges to inherently hierarchical data | MongoDB, DynamoDB |
| Tabular reporting for BI | BI tools expect tables, not graphs | Data warehouse + BI layer |
