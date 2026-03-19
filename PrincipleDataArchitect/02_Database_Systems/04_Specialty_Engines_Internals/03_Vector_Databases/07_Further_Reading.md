# Further Reading: Vector Databases

## Essential Papers & Algorithms

*   **Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs (HNSW)**
    *   *Authors:* Yu. A. Malkov, D. A. Yashunin (2018)
    *   *Why:* The foundational paper behind almost every modern vector database index. 
    *   *Link:* [arXiv:1610.02451](https://arxiv.org/abs/1610.02451)
*   **Product Quantization for Nearest Neighbor Search**
    *   *Authors:* Herve Jegou, Matthijs Douze, Cordelia Schmid
    *   *Why:* The mechanics of how databases compress high-dimensional vectors to save massive amounts of RAM.
    *   *Link:* [IEEE TPAMI Paper](https://inria.hal.science/inria-00514462/)

## Engineering Blogs & Case Studies

*   **Vespa: Approximate Nearest Neighbor Search in Vespa**
    *   *Summary:* A masterclass blog series on how Vespa handles combining boolean logic (metadata filtering) with ANN searches at massive scale.
    *   *Search Term:* "Vespa Approximate Nearest Neighbor Search"
*   **Pinecone: Understanding HNSW**
    *   *Summary:* One of the best visual explanations of how the HNSW algorithm traverses layers and builds connections.
    *   *Search Term:* "Pinecone Hierarchical Navigable Small Worlds HNSW"
*   **Netflix: Vector Search at Netflix**
    *   *Summary:* Details how Netflix applies vector search to image similarity, utilizing algorithms before vector databases were fully commoditized. 
    *   *Search Term:* "Vector Search at Netflix Engineering"

## Official Documentation Deep Dives

*   **pgvector repository (GitHub)**
    *   *Link:* [pgvector/pgvector](https://github.com/pgvector/pgvector)
    *   *Why:* The README is a fantastic resource on index tuning (setting `m` and `ef_construction`). 
*   **Milvus Docs: Index Types**
    *   *Link:* [Milvus - Index Vector](https://milvus.io/docs/index.md)
    *   *Why:* Compares IVF (Inverted File), HNSW, and DiskANN implementations and when to choose which.

## Advanced Concepts 

*   **Reranking (Cross-Encoders vs Bi-Encoders)**
    *   *Context:* Vector DBs use Bi-Encoders (fast, single vector comparison). Real semantic accuracy requires Cross-Encoders (slow, complex interaction). Learn the paradigm shift of the "Re-ranker" step from Cohere or sentence-transformers documentation.

## Cross-References
*   Review **Search Engines (Lucene)** to deeply contrast how Inverted Indices handle exact/sparse search vs how Vector Engines handle semantic/dense search.
*   Review **B-Trees & Storage Internals** to understand the fundamental mechanics of the metadata filtering layer that must execute alongside an HNSW graph.
