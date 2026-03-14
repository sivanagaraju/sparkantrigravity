# Graph Databases Overview — Concept Overview

> Neo4j, Amazon Neptune, JanusGraph: when relationships are the data.

---

## Why This Exists

Covered in depth in [01_Data_Modeling/05_Graph_Data_Modeling](../../01_Data_Modeling/05_Graph_Data_Modeling/). This section focuses on the **engine internals** rather than the modeling concepts.

## Engine Comparison

| Feature | Neo4j | Amazon Neptune | JanusGraph | ArangoDB |
|---|---|---|---|---|
| **Model** | Property Graph | Property Graph + RDF | Property Graph | Multi-model (graph+doc+KV) |
| **Storage** | Native graph (index-free adjacency) | Custom storage on AWS | Pluggable (Cassandra, HBase, BerkeleyDB) | ArangoDB engine |
| **Query Language** | Cypher | Gremlin + SPARQL | Gremlin | AQL |
| **Deployment** | Self-hosted / Aura (cloud) | AWS managed only | Self-hosted | Self-hosted / cloud |
| **Scale** | Billions of nodes (Enterprise) | Managed scaling | Distributed via backend | Cluster mode |
| **ACID** | ✅ Full transactions | ✅ | ⚠️ Depends on backend | ✅ |

## Native vs Non-Native Storage

**Native** (Neo4j): Each node physically stores pointers to adjacent nodes. Traversal = following pointers (O(1) per hop). No index lookup needed.

**Non-Native** (JanusGraph over Cassandra): Graph stored as adjacency lists in a KV store. Traversal = key lookup per hop (O(log n)). More flexible storage, but slower traversal.

## Interview — Q: "When would you choose Neptune over Neo4j?"

**Strong Answer**: "Neptune when you're already on AWS and want managed infrastructure with no ops burden. Neo4j when you need the richest query language (Cypher), the Graph Data Science library (PageRank, community detection), and native graph storage for maximum traversal performance. If you need both property graph AND RDF/SPARQL, Neptune supports both models."

## References

| Resource | Link |
|---|---|
| Cross-ref: Graph Modeling | [../../../01_Data_Modeling/05_Graph_Data_Modeling](../../../01_Data_Modeling/05_Graph_Data_Modeling/) |
| Cross-ref: Neo4j Internals | [../../08_Graph_Databases/01_Neo4j_Internals](../../08_Graph_Databases/01_Neo4j_Internals/) |
