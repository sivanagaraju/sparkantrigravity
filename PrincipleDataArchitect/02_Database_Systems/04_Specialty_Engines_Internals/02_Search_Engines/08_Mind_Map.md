# 🧠 Mind Map – Search Engines
---
## How to Use This Mind Map
- **For Revision**: Review the Theory and Techniques branches to recall how Lucene indexes differ from standard RDBMS indexes.
- **For Application**: Consult Mistakes and Hands-On before implementing your cluster config or mapping file to prevent production outages.
- **For Interviews**: Rehearse the Distributed Search Architecture under Real-World Scenarios for system design interviews.

---
## 🗺️ Theory & Concepts
### Inverted Index
- **Definition**: Mathematical inverse of a standard index; maps terms (words) directly to document IDs and positional offsets.
  - O(1) or O(log N) term lookup.
  - Massive space trade-off compared to relational layouts.
### Lucene Segments
- **Immutability**: Once written, segments never change.
  - Updates are actually "mark as deleted" + "write new document to new segment."
  - Merging algorithms operate continuously in the background to condense segments and purge true deletions.
### Relevance Scoring (TF-IDF / BM25)
- **Term Frequency**: How often the word appears in the document (linear).
- **Inverse Document Frequency**: How rare the word is across all documents globally.
  - **BM25 Saturation**: Fixes TF-IDF's bias towards long documents by saturating the score curve.
### Analysis Pipeline
- **Character Filters**: Strip HTML, normalize characters.
- **Tokenizer**: Split by whitespace, commas, etc.
- **Token Filters**: Lowercase, stemming, synonyms.

---
## 🗺️ Techniques & Patterns
### T1: Hot-Warm-Cold Architecture (Logs)
- **When to use**: Managing massive time-series event data (logs/metrics).
- **Step-by-Step**:
  - 1. Ingest newly generated logs to Hot nodes (expensive NVMe SSDs).
  - 2. ILM rules force-merge indices and move to Warm nodes (HDDs) after 7 days.
  - 3. ILM snapshots data to Cold/S3 after 30 days.
- **Failure Mode**: Not using ILM results in oversharding and eventual cluster memory exhaustion.

### T2: CQRS with CDC Sync
- **When to use**: Providing search capability for heavily mutated relational data.
- **Step-by-Step**:
  - 1. Application writes strictly to RDBMS (Primary).
  - 2. Debezium captures WAL updates, writes to Kafka topic.
  - 3. Kafka Connect Sink batches writes to Elasticsearch.
  - 4. Search API queries ES; Transactional APIs query RDBMS.
- **Failure Mode**: Network partition breaking synchronization; UI showing stale data. Requires robust CDC monitoring.

---
## 🗺️ Hands-On & Code
### Strict Mapping
- Set `dynamic: strict` in mapping definition to prevent arbitrary user data from exploding field limits.
### Search After
- Replace `from: size:` with `search_after: [timestamp, _id]` using the last returned doc ID to handle millions of results efficiently.
### Edge N-Grams
- Implement specialized tokenizers for "autocomplete/typeahead" rather than doing Wildcard queries at runtime. Shifts the compute to indexing phase.

---
## 🗺️ Real-World Scenarios
### 01: The Mapping Explosion
- **The Trap**: Passing unstructured JSON events via `dynamic: true`. Millions of unique keys parsed.
- **Scale**: Small amount of data locally, but 10,000+ fields causes Master Node to crash parsing cluster state.
- **The Fix**: Enforce schema. Flatten key-value pair metrics to specific sub-objects.

### 02: Paging Death
- **The Trap**: Allowing users or scrapers to request page 10,000 via UI.
- **Scale**: 100,000th record requested horizontally across 5 shards.
- **The Fix**: Limit `from` offsets stringently (max 10,000). Force `search_after` or Scroll APIs.

---
## 🗺️ Mistakes & Anti-Patterns
### M01: Oversharding
- **Root Cause**: Creating 1 index per day with too many shards by default (5 shards per day = 1800 per year).
- **Diagnostic**: Look for thousands of shards < 1GB via CAT API.
- **Correction**: Set ILM rollovers by size (~50GB/shard). Use 1 shard for small daily indexes.

### M02: Search as System of Record
- **Root Cause**: Developers want one database, so they treat ES like Postgres.
- **Diagnostic**: Architecture places ES as the master database with critical transactional writes.
- **Correction**: Use an RDBMS for transactions, sync to ES exclusively for the read/search workload.

---
## 🗺️ Interview Angle
### System Design
- Prepare CDC to Search architecture (Postgres -> Debezium -> Kafka -> ES).
### Theory Detail
- Understand the pipeline: Text -> Analyzer -> Tokens -> Inverted Index -> Query -> BM25 Scoring -> Merge results across shards.
### What They're Testing
- Knowing when NOT to use Search (ACID compliance, point updates).

---
## 🗺️ Assessment & Reflection
- Do our current Elasticsearch indexes enforce `strict` dynamic mapping?
- What is the average shard size in our cluster? Are we victim to oversharding?
- Are we hitting the inverted index optimally, or are we compensating for poorly analyzed data via expensive runtime prefix queries?
