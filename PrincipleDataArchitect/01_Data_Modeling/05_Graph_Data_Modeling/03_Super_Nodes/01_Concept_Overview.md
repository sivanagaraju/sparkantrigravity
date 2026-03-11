# Super Nodes — Concept Overview

> The Achilles' heel of graph databases: what happens when one node has 10 million edges.

---

## Why This Exists

**The problem**: In any real-world graph, degree distribution follows a power law (Zipf's law). Most nodes have few connections, but a tiny fraction have millions. A celebrity on Twitter has 100M followers. A popular product has 50M reviews. A shared public WiFi IP address connects 500K accounts.

When you traverse a super node, the graph engine must examine ALL its edges. A `MATCH (celeb)-[:FOLLOWS]->(other)` query on a node with 100M edges is a full table scan in disguise. It defeats the O(1)-per-hop promise of graph databases.

## Mindmap

```mermaid
mindmap
  root((Super Nodes))
    What Is a Super Node?
      Node with disproportionately high degree
      Typically top 0.01% of nodes
      Millions of edges
      Power law distribution
    Examples
      Celebrity Twitter account
      Popular product in review graph
      Shared corporate email domain
      Public WiFi IP in fraud graph
      Root category in taxonomy
    Why They're Dangerous
      Traversal becomes O(n) not O(1)
      Memory pressure loading all edges
      Lock contention on writes
      Query timeout on reads
    Mitigation Strategies
      Partitioning the super node
      Capping traversal depth
      Pre-aggregating edge counts
      Bidirectional BFS
      Filtering by edge properties
      Virtual super node indirection
```

## Key Terminology

| Term | Definition |
|---|---|
| **Super Node** | A node whose degree (edge count) is orders of magnitude higher than the median |
| **Degree Distribution** | The statistical distribution of edge counts across all nodes (usually power-law) |
| **Dense Node** | Neo4j's term for a node stored with a different internal format to handle high-degree |
| **Fan-Out** | The number of edges traversed when expanding from a node |
