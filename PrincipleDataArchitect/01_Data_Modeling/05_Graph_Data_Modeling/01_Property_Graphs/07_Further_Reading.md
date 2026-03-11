# Property Graphs — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *The Property Graph Database Model* | Angles, Gutierrez | 2018 | <https://dl.acm.org/doi/10.1145/3183713.3190657> |
| *GQL Standard — ISO/IEC 39075* | ISO/IEC JTC 1/SC 32 | 2024 | <https://www.gqlstandards.org/> |
| *Graph Pattern Matching in GQL and SQL/PGQ* | Deutsch et al. | 2022 | <https://dl.acm.org/doi/10.1145/3514221.3526057> |
| *TAO: Facebook's Distributed Data Store for the Social Graph* | Bronson et al. (Meta) | 2013 | <https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson> |
| *UniStore: A Unified Storage for Graph and Relational Data* | Various | 2023 | <https://dl.acm.org/doi/10.14778/3611479.3611521> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *Graph Databases* (2nd Ed) | Ian Robinson, Jim Webber, Emil Eifrem | 978-1491930892 | Ch 3 (property graph model), Ch 4 (data modeling), Ch 6 (Cypher) |
| *Graph-Powered Machine Learning* | Alessandro Negro | 978-1617295645 | Ch 2 (graph models), Ch 5 (fraud detection), Ch 8 (recommendations) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 2 (data models — graph section) |
| *Knowledge Graphs* | Aidan Hogan et al. | 978-3031018312 | Ch 3 (graph data models), Ch 8 (property graphs vs RDF) |
| *Graph Algorithms* | Mark Needham, Amy Hodler | 978-1492047674 | Ch 4 (centrality), Ch 5 (community), Ch 6 (pathfinding) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *TAO: The Power of the Graph* | Meta Engineering | <https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/> |
| *How LinkedIn Uses Graph to Connect 900M Members* | LinkedIn Engineering | <https://engineering.linkedin.com/blog/topic/graphs> |
| *Real-Time Fraud Detection with Graph* | PayPal Engineering | <https://medium.com/paypal-tech/real-time-graph-based-fraud-detection-at-paypal-c0e2c1d89e04> |
| *Neo4j Performance Tuning* | Neo4j Developer Blog | <https://neo4j.com/developer/performance/> |
| *Graph Databases at Airbnb* | Airbnb Engineering | <https://medium.com/airbnb-engineering/tagged/graph> |
| *Apache AGE: Graph on PostgreSQL* | Apache AGE | <https://age.apache.org/> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Graph Thinking* | Emil Eifrem | GraphConnect | <https://www.youtube.com/results?search_query=emil+eifrem+graph+thinking> |
| *Building Knowledge Graphs at Scale* | Various | KDD | <https://www.youtube.com/results?search_query=knowledge+graph+kdd> |
| *Fraud Detection with Graphs* | Various | GraphSummit | <https://www.youtube.com/results?search_query=fraud+detection+graph+database> |
| *GQL: The ISO Standard for Graph Query* | Various | SIGMOD | <https://www.youtube.com/results?search_query=gql+iso+standard+graph> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `neo4j/neo4j` | Neo4j graph database | <https://github.com/neo4j/neo4j> |
| `apache/tinkerpop` | Apache TinkerPop (Gremlin) | <https://github.com/apache/tinkerpop> |
| `apache/age` | Apache AGE — graph extension for PostgreSQL | <https://github.com/apache/age> |
| `tigergraph/ecosys` | TigerGraph ecosystem tools | <https://github.com/tigergraph/ecosys> |
| `graphframes/graphframes` | Spark GraphFrames (graph analytics on Spark) | <https://github.com/graphframes/graphframes> |
| `networkx/networkx` | Python graph library (analysis, not DB) | <https://github.com/networkx/networkx> |
| `jgraph/drawio` | Diagramming tool with graph layout algorithms | <https://github.com/jgraph/drawio> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **Neo4j** | Cypher Manual | <https://neo4j.com/docs/cypher-manual/current/> |
| **Neo4j** | Data Modeling Guide | <https://neo4j.com/docs/getting-started/data-modeling/> |
| **Amazon Neptune** | Getting Started | <https://docs.aws.amazon.com/neptune/latest/userguide/> |
| **TigerGraph** | GSQL Language Reference | <https://docs.tigergraph.com/gsql-ref/current/> |
| **Apache TinkerPop** | Gremlin Documentation | <https://tinkerpop.apache.org/docs/current/reference/> |
| **Apache AGE** | Getting Started | <https://age.apache.org/age-manual/master/intro/setup.html> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Fraud Detection Schemas** | `05_Graph_Data_Modeling/02_Fraud_Detection_Schemas/` | Primary graph application — pattern matching for fraud |
| **Super Nodes** | `05_Graph_Data_Modeling/03_Super_Nodes/` | Critical performance challenge in property graphs |
| **Data Vault Hubs & Links** | `03_Data_Vault_2_0_Architecture/` | Data Vault's hub-link-satellite pattern is conceptually similar to a graph's node-edge-properties |
| **Logical Domain Modeling** | `01_Logical_Domain_Modeling/` | Entity-relationship modeling shares conceptual roots with graph modeling |
