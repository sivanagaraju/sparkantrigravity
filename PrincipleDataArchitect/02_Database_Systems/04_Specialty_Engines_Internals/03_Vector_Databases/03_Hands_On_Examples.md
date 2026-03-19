# Hands-On Examples: Vector Databases

## 1. Physical Table Structure and Indexing Using pgvector (PostgreSQL)

If your data scale is under 100 million vectors, dedicated vector databases are often overkill. The `pgvector` extension for Postgres has become the de-facto standard for transactional + vector workloads.

```sql
-- Enable the extension in your Postgres instance
CREATE EXTENSION IF NOT EXISTS vector;

-- DDL for our Knowledge Base chunks
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL,
    tenant_id UUID NOT NULL,   -- Essential for pre-filtering (multi-tenancy)
    chunk_index INT NOT NULL,
    text_content TEXT NOT NULL,
    
    -- In pgvector, we strictly define the dimension size (e.g., 1536 for OpenAI)
    embedding vector(1536) NOT NULL
);

-- CREATE THE HNSW INDEX
-- You must index ONLY after you have some data to calculate realistic graph parameters, 
-- or specify standard defaults. 
-- 'm' is max connections per node. 'ef_construction' determines graph quality/build time.
-- Note: 'vector_cosine_ops' sets the distance metric to Cosine Similarity.
CREATE INDEX idx_hnsw_document_chunks_embedding 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- CREATE METADATA INDEX
-- Highly crucial for filtered vector search.
CREATE INDEX idx_document_chunks_tenant_id ON document_chunks(tenant_id);
```

## 2. The Vector Search Query (Cosine Similarity + Filtering)

This is how a semantic search looks in SQL using `pgvector`. The `<=>` operator computes the cosine distance (which is `1 - cosine_similarity`).

```sql
-- The application receives the [0.123, -0.045...] vector from the OpenAI API first.
SELECT 
    document_id,
    text_content,
    1 - (embedding <=> '[0.123, -0.045, ... 1536 floats]'::vector) AS similarity_score
FROM 
    document_chunks
WHERE 
    tenant_id = 'a1b2c3d4-e5f6-7890-1234-56789abcdef0' -- Pre-filter first!
ORDER BY 
    embedding <=> '[0.123, -0.045, ... 1536 floats]'::vector -- Find nearest neighbors
LIMIT 5; -- Return Top K
```

## 3. Python Orchestration (The RAG Ingestion Pipeline)

A minimal, production-like orchestration script using standard tooling to get data *into* the database.

```python
import psycopg2
from openai import OpenAI
import tiktoken

client = OpenAI(api_key="your_api_key")
conn = psycopg2.connect("dbname=postgres user=postgres password=mysecret")

def process_and_ingest_document(doc_id: str, tenant_id: str, raw_text: str):
    # 1. Chunking logic (simplified: split by paragraphs for demonstration)
    # Production uses recursive character chunking via libraries like LangChain/LlamaIndex
    chunks = raw_text.split('\n\n')
    
    # 2. Batch Embedding Generation to save network latency
    # Do NOT embed one chunk at a time.
    response = client.embeddings.create(
        input=chunks,
        model="text-embedding-3-small" # Returns 1536 dims
    )
    
    # 3. Bulk Insert into pgvector
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO document_chunks (document_id, tenant_id, chunk_index, text_content, embedding)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Execute batch insert
        args = []
        for i, (chunk, embed_data) in enumerate(zip(chunks, response.data)):
            # convert list of floats to Postgres vector string representation
            vector_str = "[" + ",".join(map(str, embed_data.embedding)) + "]"
            args.append((doc_id, tenant_id, i, chunk, vector_str))
            
        from psycopg2.extras import execute_batch
        execute_batch(cur, insert_query, args)
        
    conn.commit()
```

## Before vs. After: The Pre-Filtering Problem

**Bad Approach: Post-Filtering**
```sql
-- ANN finds the top 100 closest vectors GLOBALLY.
WITH knn_results AS (
    SELECT id, tenant_id FROM document_chunks
    ORDER BY embedding <=> '[...]' LIMIT 100
)
-- THEN filters by tenant. 
-- If only 2 out of the 100 globally closest vectors belong to this tenant, 
-- you requested K=10 but you only get 2 results returned. The UX is broken.
SELECT * FROM knn_results WHERE tenant_id = 'my-tenant-id' LIMIT 10;
```

**Correct Approach: Pre-Filtering / Single-Stage Filtering**
```sql
-- The Postgres planner uses the tenant_id B-Tree index to create a bitset.
-- During the HNSW graph traversal, nodes not in the bitset are skipped.
-- You are guaranteed to get exactly 10 results belonging to 'my-tenant-id'.
SELECT * FROM document_chunks 
WHERE tenant_id = 'my-tenant-id' 
ORDER BY embedding <=> '[...]' LIMIT 10;
```
