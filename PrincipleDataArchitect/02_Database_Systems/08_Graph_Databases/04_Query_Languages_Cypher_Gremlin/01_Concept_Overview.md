# Query Languages: Cypher vs Gremlin — Concept Overview

> Declarative (Cypher) vs imperative (Gremlin): choosing the right graph query language.

## Comparison

| Feature | Cypher | Gremlin | GQL (ISO) |
|---|---|---|---|
| **Style** | Declarative (SQL-like) | Imperative (step-by-step) | Declarative |
| **Learning Curve** | ✅ Easy (SQL developers) | ⚠️ Steeper | Medium |
| **Pattern Matching** | ✅ Native (`MATCH (a)-[:KNOWS]->(b)`) | Manual traversal steps | ✅ Native |
| **Used By** | Neo4j, Memgraph | Neptune, JanusGraph, CosmosDB | ISO standard (2024) |
| **Turing Complete** | ❌ | ✅ | ❌ |

## Same Query — Two Languages

```cypher
// CYPHER: Find friends of friends
MATCH (me:Person {name:"Alice"})-[:KNOWS]->()-[:KNOWS]->(fof)
WHERE fof <> me
RETURN DISTINCT fof.name
```

```groovy
// GREMLIN: Same query, imperative style
g.V().has('Person', 'name', 'Alice')
  .out('KNOWS')
  .out('KNOWS')
  .where(neq('alice'))
  .dedup()
  .values('name')
```

## Interview — Q: "Cypher or Gremlin?"

**Strong Answer**: "Cypher for developer productivity — declarative pattern matching is intuitive for most use cases. Gremlin when you need the engine to be vendor-neutral (supported by Neptune, JanusGraph, CosmosDB) or need Turing-complete traversal logic. GQL (ISO 39075:2024) is the future standard — it's essentially Cypher standardized."

## References

| Resource | Link |
|---|---|
| [GQL Standard](https://www.iso.org/standard/76120.html) | ISO/IEC 39075:2024 |
| [openCypher](https://opencypher.org/) | Open standard for Cypher |
| [Apache TinkerPop](https://tinkerpop.apache.org/) | Gremlin framework |
