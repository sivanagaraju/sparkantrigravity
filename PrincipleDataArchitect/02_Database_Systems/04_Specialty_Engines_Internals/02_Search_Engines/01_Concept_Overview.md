# Concept Overview: Search Engine Internals

## Why This Exists

Relational databases and basic B-tree indexes are optimized for exact-match and prefix lookups. They structurally fail when confronted with full-text search, relevance ranking, stemming, synonyms, and unstructured data queries (e.g., `WHERE body LIKE '%database architecture%'` requires a full table scan).

Search engines emerged from the field of Information Retrieval (IR) to solve the problem of finding documents within massive corpora based on term frequency and semantic relevance. Doug Cutting created Apache Lucene in 1999 because there was no fast, open-source embeddable search library. Later, Elasticsearch and Apache Solr were built around Lucene to solve the distributed systems problem: scaling a single Lucene instance across a cluster for high availability and horizontal throughput.

## What Value It Provides

*   **Sub-second Full-Text Search:** O(1) or O(log N) term lookup across petabytes of text via the Inverted Index, instead of O(N) table scans.
*   **Relevance Scoring:** Returns the *best* matches, not just *all* matches, mathematically scoring documents based on TF-IDF or BM25.
*   **Language Awareness:** Handles tokenization, stemming (e.g., "running" -> "run"), and synonyms out of the box, reducing friction for end users.
*   **Analytics on High-Cardinality Data:** The structure of the inverted index combined with columnar doc values makes it exceptionally fast for aggregations and filtering in log analytics (e.g., ELK stack).

## Where It Fits

Search engines typically sit alongside a system of record as a specialized read-optimized projection. Data is ingested from a primary database (PostgreSQL, DynamoDB) via Change Data Capture (CDC) or event streams (Kafka) into the search index.

```mermaid
C4Context
    title Component Diagram: Search Engine in the Data Stack
    
    Person(User, "Client Application")
    SystemDb(PrimaryDB, "System of Record", "PostgreSQL / DynamoDB")
    SystemQueue(Kafka, "Event Bus", "Apache Kafka / Kinesis")
    
    System_Boundary(SearchStack, "Distributed Search Engine") {
        System(Coordinator, "Coordinator Node", "Query Parallelization & Reduces")
        System(DataNode1, "Data Node 1", "Lucene Shard A")
        System(DataNode2, "Data Node 2", "Lucene Shard B")
    }
    
    Rel(PrimaryDB, Kafka, "Emits change events (CDC)")
    Rel(Kafka, SearchStack, "Ingests structured docs")
    Rel(User, Coordinator, "Issues search queries")
    Rel(Coordinator, DataNode1, "Scatter")
    Rel(Coordinator, DataNode2, "Scatter")
    Rel(DataNode1, Coordinator, "Gather & Score")
```

## When To Use / When NOT To Use

### When To Use
*   **Full-Text Search:** E-commerce catalogs, documentation search, support ticket search.
*   **Log & Event Analytics:** High-volume time-series appending of wide events where users want to interactively filter on any of 100+ columns (e.g., Kibana/ELK).
*   **Complex Filtering / Faceting:** UI experiences requiring counts of results across multiple categories ("Shoes (14) > Red (3)").

### When NOT To Use
*   **System of Record:** Never use a search engine (like Elasticsearch) as your primary database. They typically lack ACID guarantees, lose data during split-brain scenarios (historically), and updates are highly inefficient.
*   **High-Frequency Updates:** Search engines are optimized for write-once/read-many. Updating a document requires a complete re-indexing of that document. For highly mutable state, use an RDBMS or Key-Value store.
*   **Deep Joins:** Search engines require denormalized data. If your domain highly relational, joining datasets at query time in Lucene is prohibitively expensive.

## Key Terminology

| Term | Precision Definition |
|---|---|
| **Inverted Index** | A data structure mapping content (terms/words) to its locations (document IDs). The mathematical inverse of a forward index. |
| **Tokenization / Analysis** | The pipeline process of converting raw text into standard terms (e.g., lowercasing, removing punctuation, stemming). |
| **TF-IDF / BM25** | Algorithms used to score relevance. Term Frequency (how often it appears in the doc) vs. Inverse Document Frequency (how rare it is across all docs). |
| **Segment** | An immutable, physical subset of a Lucene index on disk. Compactions merge smaller segments into larger ones in the background. |
| **Document Values (DocValues)** | A columnar data structure built alongside the inverted index, used specifically to optimize sorting, aggregations, and scripting. |
| **Mapping / Schema** | The definition of how fields are indexed and stored. In search, dynamic mapping often leads to explosive cardinality if not managed. |
