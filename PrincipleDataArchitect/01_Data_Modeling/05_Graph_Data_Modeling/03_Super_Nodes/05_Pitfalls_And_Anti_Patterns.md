# Super Nodes — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: No Super Node Detection Until Production Outage

**The mistake**: Building a graph application with no monitoring of degree distribution. The first time you learn about super nodes is when the database crashes.

**What breaks**: A node grows to 5M edges over months. One day, a query traverses through it, triggering an OOM or timeout cascade. By the time you detect it, the damage is done — connection pools exhausted, all queries affected.

**Detection**:

- There is no detection — that's the anti-pattern. You discover super nodes via incident.

**Fix**: Add proactive monitoring from day one:

```cypher
// Daily degree monitoring job
MATCH (n)-[r]-()
WITH n, labels(n) AS labels, COUNT(r) AS degree
WHERE degree > 50000
RETURN labels, n.name, degree
ORDER BY degree DESC;
```

Set alerts at 100K edges (warning) and 1M edges (critical). Track degree distribution as a time series in Grafana.

---

## Anti-Pattern 2: Modeling High-Cardinality Attributes as Nodes

**The mistake**: Creating a `:Country` or `:Gender` or `:Status` node and linking millions of entities to it. The "United States" node becomes a 50M-edge super node.

**What breaks**: Any graph query that traverses through the attribute node explodes. "Find customers in the US who share a phone number" becomes a 50M × 50M Cartesian product.

**Detection**:

```cypher
// Find attribute nodes connected to >10% of all nodes
MATCH (n)-[r]-()
WITH n, labels(n) AS labels, COUNT(r) AS degree
ORDER BY degree DESC
LIMIT 20
RETURN labels, n.name, degree,
       toFloat(degree) / (MATCH (m) RETURN COUNT(m)) AS pct_of_graph;
// If pct_of_graph > 0.1 (10%), it should probably be a property, not a node.
```

**Fix**: Convert high-cardinality-but-low-uniqueness attributes to node properties:

```cypher
// ❌ WRONG: Country as a node
// (:Customer)-[:LOCATED_IN]->(:Country {name: "United States"})
// The Country node has 50M edges

// ✅ CORRECT: Country as a property
// (:Customer {country: "United States"})
// No super node. Filter by property index.
CREATE INDEX customer_country FOR (c:Customer) ON (c.country);
```

**Rule of thumb**: If the node has <100 distinct values (countries, statuses, categories), make it a property with an index. If it has high uniqueness (like city with 100K+ distinct values), it can be a node.

---

## Anti-Pattern 3: Unbounded Variable-Length Paths Through Potential Super Nodes

**The mistake**: Writing `MATCH (a)-[:FOLLOWS*]->(b)` without any depth limit or intermediate count limit, where the path may pass through super nodes.

**What breaks**: Variable-length paths explore all possible routes. Through a super node, this is combinatorial explosion: O(k^d) where k = super node degree and d = max path length.

**Fix**: Always bound and limit:

```cypher
// ✅ Bounded depth + intermediate limit
MATCH (a:User {id: 42})-[:FOLLOWS]->(intermediate)
WITH intermediate LIMIT 500  // Cap first hop
MATCH (intermediate)-[:FOLLOWS]->(b)
WHERE b <> a
RETURN DISTINCT b.name LIMIT 100;
```

---

## Anti-Pattern 4: Applying PageRank Without Super Node Treatment

**The mistake**: Running PageRank on a graph with super nodes using default parameters. The super nodes dominate the results.

**What breaks**: PageRank distributes "importance" through edges. A celebrity with 10M followers sends PageRank to 10M nodes. After a few iterations, the celebrity and their immediate neighbors dominate the top ranks — pushing genuinely important nodes out of the results.

**Detection**:

- After PageRank: check if top-20 results are all within 2 hops of the highest-degree node
- Compare PageRank results with and without super nodes

**Fix**: Two approaches:

1. **Remove super nodes before PageRank**: Exclude nodes with degree >100K from the computation. Assign them a fixed rank.
2. **Damped PageRank**: Use personalized PageRank with higher reset probability (0.3 instead of 0.15) to reduce the influence of distant super nodes.

---

## Anti-Pattern 5: Not Using Relationship Type Filtering for Super Nodes

**The mistake**: Neo4j 5+ groups relationships by type. But queries that use `(n)-[r]-()` (all types) bypass this optimization and iterate all edges.

```cypher
// ❌ WRONG: Untyped relationship pattern
MATCH (n:User {id: 42})-[r]->(other)
RETURN type(r), other.name;
// If User 42 has 1M FOLLOWS + 50 KNOWS + 20 WORKS_AT,
// this iterates all 1,000,070 edges

// ✅ CORRECT: Typed relationship pattern
MATCH (n:User {id: 42})-[r:KNOWS|WORKS_AT]->(other)
RETURN type(r), other.name;
// Only iterates 70 edges (KNOWS + WORKS_AT groups)
```

**Fix**: Always specify relationship types in queries. This is especially critical for super nodes where the edge list has multiple types with vastly different cardinalities.

---

## Decision Matrix — Super Node Handling Strategies

| Node Degree | Strategy | Latency Impact | Complexity |
|---|---|---|---|
| < 10K | No action needed | Negligible | None |
| 10K – 100K | Add query timeout + monitoring | Monitor P99 | Low |
| 100K – 1M | Edge type partitioning + intermediate LIMIT | Moderate queries use cache | Medium |
| 1M – 10M | Pre-computed cache + degree-aware routing | Live traversal impossible — cache only | High |
| 10M+ | Dedicated serving path (FlockDB-style) | No graph traversal at all | Very high |
