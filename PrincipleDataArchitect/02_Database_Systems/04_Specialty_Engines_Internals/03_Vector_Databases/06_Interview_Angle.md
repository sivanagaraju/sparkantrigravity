# Interview Angle: Vector Databases

## How This Appears

In 2024+, Vector Database questions are the fastest-growing subcategory in System Design interviews. They manifest in prompts like: "Design a RAG system for an internal enterprise wiki," "Design a Semantic Search Engine for Pinterest," or "How would you handle document retrieval for a chatbot?"

## Sample Questions & Answer Frameworks

### Q1: "Explain the difference between Exact k-NN and Approximate Nearest Neighbor (ANN). Why don't we just use k-NN for everything?"

*   **Weak Answer (Senior):** "Exact k-NN checks every single vector, which is too slow. ANN is faster but sometimes misses the exact best match."
*   **Strong Answer (Principal):** "k-NN is O(N * D) where N is dataset size and D is dimensionality. For 1 billion 1536-dimensional vectors, every search requires 1.5 trillion floating-point operations. It's unscalable and causes extreme latency. We use ANN algorithms like HNSW, which pre-computes an interconnected graph. HNSW provides O(log N) search complexity. The trade-off is recall (e.g., we might only find the true nearest neighbor 98% of the time instead of 100%) and a massive increase in baseline RAM consumption to hold the graph indices in memory."
*   **What They're Testing:** Complexity analysis (Big O), hardware realities (Floating point ops), and identifying the principal trade-offs (Speed vs Recall vs RAM).

### Q2: "How would you architect a RAG system for a multi-tenant SaaS application where users must NOT see each other's data?"

*   **Weak Answer:** "I will add a `tenant_id` to the vector metadata. I'll query the vector database for the top 50 results based on the search query, then use a code filter in my backend loop to drop any results that don't match the current user's `tenant_id`."
*   **Strong Answer:** "That architecture creates the Post-Filtering Trap. If a user has a small footprint, none of their documents might appear in the top 50 globally, resulting in a blank screen. I would use an engine that supports Single-Stage Filtered Search (like Pinecone or pgvector). I would pass `tenant_id` as a pre-filter query parameter to the database. The database uses a standard B-Tree index to create a bitset of allowed document IDs for that tenant, and strictly uses that bitset to restrict pathways *during* the HNSW graph traversal. For extreme multi-tenant isolation scenarios, I would dynamically provision separate logical indices or namespaces per tenant."
*   **What They're Testing:** Understanding the post-filtering zero-result flaw and securing multi-tenant data structures at the DB level.

### Q3: "Our vector index has grown to 5 TB. We are getting OOM kills. How do you fix this?"

*   **Weak Answer:** "Scale up the database nodes to instances with more RAM."
*   **Strong Answer:** "First, apply Scalar Quantization (SQ) or Product Quantization (PQ) to compress the embeddings from float32 to int8 or smaller. This instantly cuts memory by 4x to 64x with marginal recall loss. Second, eliminate 'fat vectors'—ensure we are only storing the vector and a UUID in the vector DB, placing the raw text payloads in S3 or Postgres. If we still exceed memory limits, we must migrate to a tiered storage architecture using memory mapping (`mmap`), utilizing NVMe SSDs to page the graph on disk rather than holding it entirely in RAM."
*   **What They're Testing:** Deep mechanics of vector footprints, optimization via mathematics (Quantization), and tiered hardware leverage.

## Whiteboard Exercise

**The Two-Stage Enterprise RAG Pipeline**

Practice drawing the evolution from a naive one-stage vector search to a production two-stage recall/rerank pipeline.

```mermaid
graph LR
    subgraph 1. Retrieval (Recall)
    Q[Search Query] --> VDB[(Vector DB <br/> HNSW Index)]
    VDB -- Top 100 Vectors --> ReRank
    end
    
    subgraph 2. Precision (Rerank)
    ReRank[Cross-Encoder Reranker <br/> e.g., Cohere] -- Rescores based on <br/> deep semantic <br/> interaction --> Cutoff
    Cutoff[Top 5 Strict Match] --> LLM
    end
    
    subgraph 3. Generation
    LLM[LLM Context Window] --> Output
    end
```

*Narrative to practice:* "A single vector embedding reduces nuanced sentences into a point in space, losing precision. To fix this at scale, we use a two-stage pipeline: we use the Vector DB with a fast Embedding model as a cheap 'net' to retrieve the top 100 documents. Then, we pass those 100 documents through a Cross-Encoder Reranking model, which is highly accurate but computationally heavy, to sort them precisely before passing the final Top 5 to the Generator LLM."
