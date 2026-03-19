# Pitfalls & Anti-Patterns: Graph Databases

## 1. The Supernode Problem (The Dense Hub)

A supernode is a vertex with a disproportionately high number of edges (e.g., millions). In a transaction graph, a node for "USD Currency" or a node representing a massive centralized exchange wallet will be a supernode.

*   **Symptom**: Traversals that touch a specific node suddenly take minutes or cause OOM errors. The graph database halts on simple queries.
*   **Detection**: Run profiling queries. Calculate the mathematical degree distribution of your graph (`MATCH (n) RETURN size((n)-->()) AS connections ORDER BY connections DESC LIMIT 5`).
*   **Fix**: Do not create generic, low-cardinality nodes. Instead of connecting every user to a single `(c:Country {name: 'USA'})` node, store `country: 'USA'` as a property directly on the User node. Extract aggregate counts into properties rather than relying on counting edges at runtime.

## 2. Unbounded Variable-Length Paths

Permitting queries to traverse an infinite depth to find a path between two nodes. 

`MATCH (a:Person {name: 'Alice'})-[*]-(b:Person {name: 'Bob'}) RETURN path`

*   **Symptom**: CPU spikes to 100%, query runs until it exhausts memory or hits a strict timeout.
*   **Detection**: Look for `[*]` or omitting edge directions `-(b)` in the slow query log. In highly interconnected networks (small-world graphs), a 6-hop query touches practically the entire database.
*   **Fix**: **Always** enforce bounded depths and directionality. `MATCH (a)-[:KNOWS*1..3]->(b)`.

## 3. Treating the Graph Database as an Object Store

Because graphs are "schemaless," developers often dump entire JSON documents into Node properties (e.g., placing base64 images, 10,000-character text blocks, or heavily nested strings inside a node).

*   **Symptom**: High disk I/O, cache thrashing. Graph operations are fast only if the node and relationship blocks fit efficiently in the RAM page cache. Pumping massive blobs into nodes evicts topological data from RAM.
*   **Detection**: Node property storage size vastly outweighs relationship storage size. 
*   **Fix**: Graph DBs should only hold data that is queried, traversed, or filtered on. Store large textual/blob payloads in S3/DynamoDB/Postgres, keeping only the UUID pointer in the Graph node.

## 4. Modeling Events as Properties Instead of Nodes

Storing transactional history as dynamic properties or arrays on a Node or Edge, rather than as actual Nodes. 
*(e.g., Updating `account.balance_history = [10, 20, 50]` instead of creating a `(Transaction)` node.)*

*   **Symptom**: Complex analytic queries become impossible to write in Cypher without using heavy projection functions. Lost traceability.
*   **Fix**: Use the **Event-Based Graph** pattern. Actions mapping to a point in time should act as standalone nodes (e.g., `(User)-[:BOUGHT]->(Order)-[:CONTAINS]->(Product)`).

## Decision Matrix: When is a Graph DB the WRONG Choice?

| Scenario | Why Graphs Fail | Choose Instead |
|---|---|---|
| **Heavy Aggregations (OLAP)** | "Select sum(revenue) group by region". The graph must traverse every node sequentially in memory. It lacks vectorized columnar scans. | ClickHouse, Snowflake, BigQuery |
| **Simple KV / CRUD operations** | "Get User Profile 123". Fetching a single node takes the same time as fetching a row, but you are paying a massive overhead for the graph software licensing and RAM footprint. | DynamoDB, Redis, PostgreSQL |
| **Time-Series / Logging** | Log events rarely point to each other in complex cyclical networks. They are simply appended isolated events. | InfluxDB, Elasticsearch / Apache Pinot |
| **Massive Batch Writes (ETL)** | Ingesting 1 billion rows into an RDBMS is fast. Ingesting 1 billion nodes and establishing the physical index-free adjacency pointers for 3 billion edges is computationally brutal and slow. | Relational DB / Data Lake |
