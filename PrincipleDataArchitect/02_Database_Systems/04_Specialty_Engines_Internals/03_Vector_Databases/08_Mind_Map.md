# 🧠 Mind Map – Vector Databases
---
## How to Use This Mind Map
- **For Revision**: Differentiate between Sparse Search (BM25) and Dense Search (Vectors). Memorize HNSW layer mechanics.
- **For Application**: Implement the Pointer Pattern (keep payloads out of vector index) and ensure Single-Stage Filtering is configured for multi-tenant apps.
- **For Interviews**: Rehearse the Two-Stage Retrieval pipeline (Recall via VDB -> Precision via Reranker) for all RAG system design questions.

---
## 🗺️ Theory & Concepts
### Vector Embeddings
- **Definition**: Floating-point arrays representing latent semantic meaning output by transformer models.
  - O(log N) search using Approximate Nearest Neighbors (ANN).
  - High dimensionality (e.g., 1536) enables nuance but costs RAM.
### Distance Metrics
- **Cosine Similarity**: Measures vector angle. Ignores magnitude. Standard for NLP.
- **Euclidean (L2)**: Measures straight-line distance. Good for computer vision matching.
- **Dot Product**: Measures angle and magnitude. Fastest to compute if vectors are normalized.
### Exact k-NN vs ANN
- **Exact k-NN**: Brute force. Scans every record. Perfect accuracy, abysmal O(N) performance.
- **ANN (HNSW)**: Approximate. Builds skiplist graphs. Fast O(log N) speed, high RAM usage, slight accuracy hit (~95-99% recall).

---
## 🗺️ Techniques & Patterns
### T1: Single-Stage Post-filtering (Pre-Filtering)
- **When to use**: Executing queries that have strict constraints (e.g., specific user ID, date range).
- **Step-by-Step**:
  - 1. Standard B-Tree queries metadata and creates an allowed Bitset.
  - 2. HNSW traversal begins.
  - 3. Algorithm checks node against Bitset and safely ignores unauthorized graph nodes.
- **Failure Mode**: Performing "Post-Filtering" at the application code layer leads to 0 results returned.

### T2: The Two-Stage RAG Pipeline
- **When to use**: High-accuracy enterprise AI chatbots.
- **Step-by-Step**:
  - 1. **Recall**: Vector DB uses fast embeddings to fetch Top 100 loose matches.
  - 2. **Precision**: Cross-encoder reranker scores the 100 matches intricately, dropping 95.
  - 3. **Generation**: Top 5 injected into LLM context window.
- **Failure Mode**: Stuffing 100 un-ranked vector results into the LLM causes "Lost in the middle" hallucination syndrome.

---
## 🗺️ Hands-On & Code
### pgvector Basics
- `CREATE EXTENSION vector;`
- Store explicitly: `embedding vector(1536)`
- Must generate index *after* data is present to optimize graph: `CREATE INDEX ... USING hnsw(embedding vector_cosine_ops)`
### Quantization
- **Scalar Quantization (SQ)**: Convert float32 to int8. 4x RAM reduction.
- **Product Quantization (PQ)**: Cluster vectors into sub-spaces. Up to 64x RAM reduction.

---
## 🗺️ Real-World Scenarios
### 01: The HNSW Memory OOM
- **The Trap**: Assuming vector databases scale linearly on disk like Postgres.
- **Scale**: Graphs require being resident in RAM. 500M vectors = hundreds of GBs of RAM.
- **The Fix**: Apply Scalar Quantization + utilize Memory-Mapped (mmap) files backed by NVMe to paginate memory.

### 02: Spotify Annoy Scale
- **The Trap**: Cross-referencing 100M users against 50M songs via matrix multiplication to generate Discover Weekly.
- **Scale**: Brute force mathematically impossible.
- **The Fix**: Used Random Projection Trees (Annoy algorithm) that could be mmap'd across Python processes to save clustered memory.

---
## 🗺️ Mistakes & Anti-Patterns
### M01: Fat Vectors
- **Root Cause**: Storing full 2MB PDF text chunks in the metadata payload next to the vector inside the VDB.
- **Diagnostic**: Vector indices consuming more RAM than the raw relational database.
- **Correction**: Store ONLY the vector and a UUID in the Vector DB (Pointer Pattern). Hydrate the full text from S3/Postgres post-search.

### M02: Incoherent Chunking
- **Root Cause**: Blindly slicing text strictly by character limits (e.g., cutting sentences in half) before embedding.
- **Diagnostic**: High technical vector similarity retrieved, but the actual human sentence returned is useless ("...and therefore it is.")
- **Correction**: Semantic chunking and metadata prepending. Allow 10% token overlap between chunks.

---
## 🗺️ Interview Angle
### System Design
- RAG pipeline design (Document -> Chunk -> Embed -> HNSW -> Rerank -> LLM).
- Trade-offs: When to use full text search (Lucene) vs semantic search (Vectors). (Answer: Use a Hybrid search approach combining both).
### Big-O Focus
- Deep understanding of O(log N) HNSW speeds versus O(N*D) k-NN matrix multiplication speeds.

---
## 🗺️ Assessment & Reflection
- Does our RAG application filter by metadata before or after the vector search limit is applied?
- Are we hitting OOM limits? If so, have we instituted scalar quantization?
- Are we utilizing Hybrid Search, combining BM25 exact match scores with Vector Semantic scores for optimal relevance?
