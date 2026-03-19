# Pitfalls & Anti-Patterns: Vector Databases

## 1. Fat Vectors (Storing Massive Payloads in the DB)

Developers treat the Vector Database like a document store, appending the entire raw PDF text, base64 images, and massive JSON structures in the metadata payload alongside the vector.

*   **Symptom**: Astronomical memory usage (RAM) and severely degraded search latencies, as the architecture attempts to cache large payloads alongside graph pointers.
*   **Detection**: Metadata size per record is significantly larger than the vector size itself (a 1536-dim vector is exactly 6KB; metadata over 5KB is a red flag).
*   **Fix**: **The Pointer Pattern**. Store only the vector, the tenant_id, and a `document_id` UUID in the Vector DB. Perform the vector search to get the Top K UUIDs, then `SELECT * FROM postgres WHERE id IN (uuid1, uuid2...)` to fetch the heavy textual payloads.

## 2. Defaulting to Brute-Force (k-NN) or Exact Match

Ignoring the index structure, or failing to realize the database hasn't built the HNSW index yet (pgvector requires manual index creation).

*   **Symptom**: Vector queries taking 500ms+ sequentially and CPU usage spiking to 100%.
*   **Detection**: Running `EXPLAIN ANALYZE` on the query shows a `Seq Scan` rather than an `Index Scan`.
*   **Fix**: Ensure `hnsw` or `ivfflat` indices are created. For `pgvector` specifically, the index cannot be used if the query asks for more vectors (e.g., `LIMIT 100`) than the parameter `ef_search` has explored. 

## 3. Disjointed Chunking & Embedding 

Embedding text completely out of context. For example, splitting a document arbitrarily by sentence. The sentence "It failed." is embedded. When a user searches "Why did the login API crash?", the vector for "It failed" has zero mathematical similarity to the query.

*   **Symptom**: Vector database returns extremely poor relevance scores. "Garbage in, garbage out".
*   **Detection**: Manual review of the chunks being output by the processing pipeline. 
*   **Fix**: Implement context-aware chunking. Append metadata to the text *before* embedding (e.g., embed the string: `Document: Login Service Outage 2024. Content: It failed.`). Ensure chunking has token overlap (e.g., 500 token chunk with 50 token overlap).

## 4. The Post-Filtering Trap

Executing a vector search first to find the 100 nearest neighbors globally, and then applying metadata filters (like date ranges or user ID) in the application layer.

*   **Symptom**: A user searches their personal library, you request Top K=10, but the result returns 0 documents, even though they have documents that match. 
*   **Reasoning**: The user's documents were ranked 101st and 102nd globally, and were cut off in the Top 100 vector search before the filter was applied.
*   **Fix**: You must use a database that supports **Single-Stage Filtered Search** (pre-filtering), where the internal HNSW graph traversal respects the metadata bitset *during* the graph walk.

## Decision Matrix: Is a Vector Database the WRONG Choice?

| Scenario | Why Vectors Fail | Choose Instead |
|---|---|---|
| **Exact SKU/ID lookup** | "Find me product AB-123-X". Vectors search for semantic neighbors. "AB-123-Y" will score identically to X, returning wrong exact items. | Relational DB / Redis |
| **High Frequency Updates** | HNSW graphs are extremely brittle to constant updates. Node connections must be broken and re-woven. | Cassandra / DynamoDB |
| **Small scale data (< 1M rows)** | Spinning up a dedicated Milvus/Pinecone cluster adds network hops and architectural burden for data that fits in 1GB. | pgvector on your existing Postgres |
| **Complex Joins required** | You cannot perform an OLAP JOIN across two sets of 1536-dimensional spaces at query time. | Denormalize data at ingestion time |
