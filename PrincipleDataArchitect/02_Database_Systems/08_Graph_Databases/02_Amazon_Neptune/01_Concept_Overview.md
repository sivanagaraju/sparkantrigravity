# Amazon Neptune — Concept Overview

> AWS-managed graph database supporting both Property Graph (Gremlin) and RDF (SPARQL).

## Neptune vs Neo4j

| Feature | Neptune | Neo4j |
|---|---|---|
| **Deployment** | AWS managed only | Self-hosted / Neo4j Aura |
| **Query Language** | Gremlin + SPARQL + openCypher | Cypher (native) |
| **Graph Model** | Property Graph + RDF | Property Graph only |
| **Scaling** | Read replicas (up to 15) | Fabric for sharding |
| **Storage** | Distributed across 3 AZs | Single machine (CE) / Cluster (EE) |
| **GDS Library** | ❌ Limited analytics | ✅ Rich graph algorithms |
| **Best For** | AWS-native, multi-model graph | Rich graph analytics, Cypher |

## References

| Resource | Link |
|---|---|
| [Amazon Neptune](https://aws.amazon.com/neptune/) | AWS Documentation |
