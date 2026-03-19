# Further Reading: Graph Databases

## Essential Books

*   **Graph Databases (O'Reilly)**
    *   *Authors:* Ian Robinson, Jim Webber & Emil Eifrem
    *   *Why:* The definitive text on applied graph data modeling and the internals of index-free adjacency. Co-written by the CEO of Neo4j.
    *   *Link:* [Free Ebook Version from Neo4j](https://neo4j.com/graph-databases-book/)
*   **Designing Data-Intensive Applications**
    *   *Author:* Martin Kleppmann
    *   *Why:* Chapter 2 contains a superb, unbiased comparison of the Relational vs. Document vs. Graph data models, and Datalog evaluation. 

## Academic Papers

*   **TAO: Facebook’s Distributed Data Store for the Social Graph**
    *   *Authors:* Nathan Bronson et al.
    *   *Why:* Facebook proved you don't need a single monolithic native graph database to support the world's largest graph. They built a C/C++ caching layer over MySQL. A mandatory read for system design.
    *   *Link:* [USENIX 2013 Paper](https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson)
*   **Spanner: Google’s Globally-Distributed Database**
    *   *Context:* While not exclusively a graph database, the interleaved table capabilities provided the foundation for distributed multi-model storage (e.g., Cloud Spanner).

## Engineering Blogs & Case Studies

*   **LinkedIn Engineering: Building the Economic Graph**
    *   *Summary:* Details how LinkedIn models over 1 billion entities (members, jobs, companies) and queries relationships in real-time.
    *   *Search Term:* "LinkedIn Engineering The Economic Graph"
*   **Uber Engineering: Using Graph Databases for Fraud**
    *   *Summary:* Explores how Uber mapped driver devices, credit cards, and GPS coordinates to identify syndicates utilizing shared devices.
    *   *Search Term:* "Uber Engineering Graph Database Fraud Detection"

## Official Documentation Deep Dives

*   **Neo4j: Under the Hood**
    *   *Why:* Excellent diagrams of the actual physical data layout on disk (linked lists of pointers).
    *   *Link:* [Neo4j Internals](https://neo4j.com/docs/getting-started/current/graph-database-concepts/graph-architecture/)
*   **Amazon Neptune Architecture**
    *   *Why:* A great comparison case. Neptune is non-native; it translates graph traversals into a columnar storage clustered execution environment. Good for contrasting with Neo4j.

## Cross-References
*   Review **Storage Engines and Disk Layout (B-Trees)** to contrast standard O(log N) indexing with O(1) Index-Free Adjacency.
*   Review **Time-Series Databases** to contrast the highly interconnected write/read patterns of graphs versus the strictly appened-only disconnected nature of metric data.
