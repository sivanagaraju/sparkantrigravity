# 🧠 Mind Map – Graph Databases
---
## How to Use This Mind Map
- **For Revision**: Cement the difference between Native (Index-Free Adjacency) and Non-Native graph storage.
- **For Application**: Review the Anti-Patterns before modeling your data to avoid Supernode traps and object-store abuse.
- **For Interviews**: Rehearse the decision matrix justifying when a recursive SQL CTE fails and Cypher/Gremlin is strictly required.

---
## 🗺️ Theory & Concepts
### Index-Free Adjacency
- **Definition**: The physical implementation of a native graph database.
  - Nodes maintain direct memory pointers to connecting edges.
  - O(1) constant time traversal per hop, completely bypassing index lookups.
### Property Graph Model
- **Mechanisms**: Nodes (Entities) and Edges (Relationships).
  - Both Nodes and Edges can contain schema-less Key-Value properties.
  - Edges are explicitly directional but can be traversed bi-directionally.
### Native vs Non-Native
- **Native**: Physically structured as a graph on disk (Neo4j, Memgraph). Maximum traversal speed, harder to horizontally scale.
- **Non-Native**: Graph translation layer over Cassandra/HBase/MySQL (JanusGraph, TAO). Easier horizontal scale, but traversal incurs network latency and index scan overhead.

---
## 🗺️ Techniques & Patterns
### T1: Event-Based Graph Modeling
- **When to use**: Capturing activity networks (Fraud, Logistical flow).
- **Step-by-Step**:
  - 1. Never model a transaction as a property on a User node.
  - 2. Create physical Nodes for events: `(User)-[:INITIATED]->(Transaction)-[:RECEIVED_BY]->(User)`
  - 3. Traverse paths across transaction nodes to identify loops or mules.
- **Failure Mode**: Overloading Node properties leading to inability to utilize graph algorithms (PageRank, Shortest Path).

### T2: Asynchronous Graph Projection
- **When to use**: Isolating critical transactions from heavy/variable graph queries.
- **Step-by-Step**:
  - 1. Complete ACID transaction in standard RDBMS.
  - 2. Replicate change via CDC (Debezium/Kafka) to Graph processing workers.
  - 3. Execute Cypher queries on the decoupled Graph cluster.
- **Failure Mode**: Attempting deep graph traversals inline with user-facing HTTP requests results in highly unpredictable response times.

---
## 🗺️ Hands-On & Code
### Cypher Basics
- `MERGE` ensures idempotencies when streaming duplicate records from Kafka.
- Variable hop syntax: `-[*1..5]->` replaces massive complex Recursive CTEs in SQL.
- Always require edge direction `->` to prune traversal scope unless necessary.

---
## 🗺️ Real-World Scenarios
### 01: The Supernode Explosion
- **The Trap**: A massive celebrity gets 10M relations. A query accidentally lands on this node.
- **Scale**: Evaluating 10 million incoming edges crushes the RAM limit and halts the query thread.
- **The Fix**: Impose strict degree-cutoffs in query planners. Offload supernode aggregate aggregations to distributed caches.

### 02: Facebook TAO Pattern
- **The Trap**: Storing billions of users on one monolithic graph DB is physically impossible.
- **Scale**: Trillions of edges across globally distributed regions.
- **The Fix**: Build a graph-query caching layer placed aggressively over horizontally sharded MySQL databases.

---
## 🗺️ Mistakes & Anti-Patterns
### M01: Infinite Traversal
- **Root Cause**: Unbounded hop count `MATCH (a)-[*]-(b)` in a dense graph.
- **Diagnostic**: Query execution time hits timeout wall. High Garbage Collection in JVM.
- **Correction**: Strictly enforce depths (`*1..4`) and directional flows.

### M02: Generic Supernodes
- **Root Cause**: Trying to centralize metadata. e.g., creating a `(USA)` node and linking 100M users to it.
- **Diagnostic**: Extreme bottlenecking when any query passes through the generic node.
- **Correction**: Refactor categorical traits as properties on the user `User {country: 'USA'}` and index the property on the B-tree.

---
## 🗺️ Interview Angle
### System Design
- **Social Networks**: Do not default to Neo4j. If it's pure scale and 1st degree lookups, Sharded DB + Caching (TAO clone) wins. If it's deep fraud ring detection, Native Graph Database wins.
### Graph Algorithms
- Understand the business use case for **PageRank** (identifying important nodes) and **Shortest Path** (logistics).

---
## 🗺️ Assessment & Reflection
- Does our schema suffer from the "Property Dump" anti-pattern where blobs are ruining the graph cache?
- Are we forcing our Postgres DB to calculate 5-deep JOINs with Recursive CTEs when a Graph implementation would be 100x faster?
- Have we safeguarded our API against users triggering unbounded graph queries?
