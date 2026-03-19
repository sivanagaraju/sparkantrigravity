# Real-World Scenarios: Distributed Search

## Case Study 1: Logging & Tracing at Scale (Uber / ELK)

**The Trap:**
Companies begin dumping all raw application logs into Elasticsearch using Logstash or Filebeat without lifecycle policies or schema enforcement. Within months, mapping explosions occur (too many unique dynamic fields per index) resulting in OOM errors and a frozen cluster.

**The Architecture & Fix:**
Uber and others utilize a strict Index Lifecycle Management (ILM) policy and Hot-Warm-Cold architecture.

*   **Production Numbers:** 10+ PB of logs, millions of events per second.
*   **Data Tiering:**
    *   **Hot Nodes:** High CPU/RAM, NVMe SSDs. Hold the last 7 days of logs. Indices are actively written.
    *   **Warm Nodes:** High Density HDD/SATA SSD. Hold 8-30 days of logs. Read-only, segments force-merged to lower resource footprint.
    *   **Cold Nodes / Cloud Storage:** Snapshot to AWS S3 / GCS. Searchable Snapshots utilized.
*   **Routing:** Logs are buffered in Kafka to absorb spikes before hitting Elasticsearch.

**Deployment Topology (Log Analytics)**

```mermaid
graph TD
    Services[Microservices] -->|Logs| Kafka[Kafka Cluster]
    Kafka --> Logstash[Logstash / Vector]
    
    subgraph "Elasticsearch Cluster"
        Coord[Coordinating Nodes]
        Master[Dedicated Master Nodes]
        
        Logstash -- Bulk Index --> Hot[Hot Data Nodes (NVMe)]
        Coord -- Search --> Hot
        Coord -- Search --> Warm[Warm Data Nodes (HDD)]
        Coord -- Search --> Cold[Cold Cluster]
        
        Hot -. ILM: Move after 7d .-> Warm
        Warm -. ILM: Snapshot after 30d .-> S3[(AWS S3)]
    end
```

## Case Study 2: E-Commerce Catalog Search (Shopify / Amazon)

**The Problem:**
Users search for "red running shoes under $100". Searching a relational database via `LIKE '%running%'` is slow and provides arbitrary ordering.

**The Fix:**
Elasticsearch acts as a secondary index exclusively for the storefront.

*   **Architecture:** The primary catalog lives in a relational DB (e.g., MySQL or Aurora). A CDC process streams inventory updates to an Elasticsearch index.
*   **Scale Numbers:** ~100M documents. Tens of thousands of read QPS. Very few write QPS compared to reads (only on price/inventory update).
*   **Relevance:** Custom scoring functions apply decay to older products, boost products with high sales velocity, and apply fuzzy matching for typos.

**Post-Mortem Scenario: The Inventory Overload**
*   *Incident:* Black Friday sale triggers rapid inventory decrements. The CDC pipeline sends millions of single-document updates to Elasticsearch. ES cluster maxes out CPU on constant Segment merging, slowing down read queries for customers.
*   *Root Cause:* Treating ES like an RDBMS and sending high-frequency point updates.
*   *Fix:* Buffer inventory updates in Memcached/Redis for instant display, and batch-update Elasticsearch every 1-5 minutes rather than on every single checkout.

## Case Study 3: The Mapping Explosion Incident

**The Problem:**
An analytics platform allowed users to push custom JSON payloads. The ES index was set to `dynamic: true`.

**What Went Wrong:**
Users started sending map keys with timestamps:
`{"event_metrics": {"2024-01-01T12:00": "click_1", "2024-01-01T12:01": "click_2"}}`
Elasticsearch dutifully created a new column (mapping) for *every single timestamp*. Upon reaching 10,000 fields, the cluster state became too massive to distribute across nodes, causing the Master node to crash and split-brain scenarios.

**The Fix:**
*   Change mappings to strict or set up dynamic templates that map unknown fields to a flattened type or text/keyword fallback.
*   Restructure the JSON to `{"timestamp": "2024-01-01T12:00", "event": "click_1"}` before ingestion.
