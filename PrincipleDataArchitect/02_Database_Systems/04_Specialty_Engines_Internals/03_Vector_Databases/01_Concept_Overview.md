# Concept Overview: Vector Databases

## Why This Exists

Historically, finding data relied on exact keyword matches (B-Trees) or token frequencies (Inverted Indices/BM25). Both fail when users search conceptually—e.g., searching for "comfortable footwear" and missing a document about "running shoes" because the literal keywords don't overlap. 

The rise of deep learning and Transformer models (BERT, GPT) enabled turning unstructured data (text, images, audio, video) into **vector embeddings**—arrays of high-dimensional floating-point numbers containing semantic meaning. A system was needed to efficiently store, index, and query these massive high-dimensional arrays using mathematical distance rather than exact equality. Vector Databases emerged to solve the *Approximate Nearest Neighbor (ANN)* problem at billion-scale.

## What Value It Provides

*   **Semantic Search:** Retrieve documents based on *meaning* and *context*, rather than exact keywords.
*   **Multimodal Queries:** Search images using text, or text using images, since both can be mapped to the same latent vector space.
*   **RAG (Retrieval-Augmented Generation):** The foundational memory layer for LLMs, allowing them to accurately answer questions over private, massive corpora.
*   **O(log N) High-Dimensional Search:** Finding the nearest neighbor among 1 billion 1536-dimensional vectors via brute force takes seconds to minutes; Vector DBs (via hardware optimization and ANN algorithms) do it in milliseconds.

## Where It Fits

Vector databases operate as a specialized secondary index or semantic retrieval layer, frequently positioned between a primary system of record and a generative AI/Machine Learning application layer.

```mermaid
C4Context
    title Component Diagram: Vector Database in the Stack
    
    Person(User, "Client / End User")
    System(App, "AI Application Layer", "RAG Pipeline / Recommender")
    SystemDb(PrimaryDB, "System of Record", "Postgres / Snowflake")
    System_Ext(LLM, "Embedding Model", "OpenAI / Cohere")
    
    System_Boundary(VectorStack, "Vector Database") {
        System(Compute, "Compute Node", "ANN Search (HNSW/IVF)")
        System(Storage, "Storage Node", "Vector & Metadata Store")
    }
    
    Rel(PrimaryDB, App, "Raw data export")
    Rel(App, LLM, "Generates embeddings for chunks")
    Rel(App, VectorStack, "Ingests Vectors + Metadata")
    
    Rel(User, App, "Natural Language Query")
    Rel(App, LLM, "Embeds Query")
    Rel(App, Compute, "Nearest Neighbor Search")
    Rel(Compute, Storage, "Read Index")
    Rel(App, User, "Synthesized Result")
```

## When To Use / When NOT To Use

### When To Use
*   **Retrieval-Augmented Generation (RAG):** Powering LLM chatbots with enterprise knowledge.
*   **Recommendation Systems:** Finding comparable products, songs, or articles by storing user/item embeddings.
*   **Deduplication / Anomaly Detection:** Finding mathematically near-identical images or logs.
*   **Semantic Search:** E-commerce search where intent matters more than exact SKU or product name matching.

### When NOT To Use
*   **Primary System of Record:** Vector databases are generally bad at high-throughput transactional (OLTP) updates. Metadata filtering is getting better, but they are not relational engines.
*   **Exact Keyword Matching is Sufficient:** If users search by UUID, exact part numbers, or structured SKUs, a B-Tree or Hash index is vastly cheaper and perfectly accurate. 
*   **Low Dimensional Data:** If you are comparing 2D/3D geospatial coordinates, use a Spatial Index (Quadtree/R-Tree/PostGIS). Vector databases are built for *high* dimensions (d > 100).

## Key Terminology

| Term | Precision Definition |
|---|---|
| **Vector Embedding** | A mathematical representation of an object (e.g., text, image) as an array of floating-point numbers (e.g., `[0.12, -0.44, ... 0.89]`). |
| **High Dimensionality** | The number of elements in the vector. OpenAI's `text-embedding-3-small` outputs 1536 dimensions. More dimensions = more nuance, but higher storage and compute cost. |
| **Distance Metric** | The mathematical function used to determine similarity. Common metrics: **Cosine** (measures angle, magnitude-agnostic), **L2 / Euclidean** (measures straight-line distance), **Dot Product** (measures angle + magnitude). |
| **k-NN (k-Nearest Neighbors)** | *Exact* search. Calculates distance between the query and *every* vector in the DB. Perfect accuracy, O(N) complexity (unusable at scale). |
| **ANN (Approximate Nearest Neighbor)** | *Heuristic* search. Trades perfect accuracy for massive speed gains. Algorithms include HNSW, IVF, and LSH. |
| **HNSW (Hierarchical Navigable Small World)** | The state-of-the-art ANN algorithm. A multi-layered graph data structure ensuring O(log N) search times, but requires significant RAM. |
| **Pre-filtering vs Post-filtering** | Applying metadata filters (e.g., `WHERE tenant_id = 'A'`) *before* or *during* the vector search (Pre-filtering / Single-Stage) vs *after* the vector search (Post-filtering). |
