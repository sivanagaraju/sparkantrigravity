# 18 — System Design & Distributed Architectures

> "There is no 'perfect' architecture. There are only trade-offs, bottlenecks, and the laws of physics."

This is the crown jewel of the curriculum. System Design at the Principal level isn't about knowing that Kafka exists—it's about knowing exactly what happens to a multi-region Kafka cluster when `us-east-1` goes down during Black Friday, and how your downstream data warehouse will handle the resulting duplicate events.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_The_Physics_of_Distributed_Systems/`

- **Latency Numbers Every Architect Should Know**: L1 cache to global network packets. Designing with the speed of light in mind.
- **Idempotency as a First Principle**: Architecting systems under the assumption that network requests will fail and retry. "Exactly-once" vs. "At-least-once" message delivery.
- **Backpressure & Circuit Breakers**: Designing choke points so an unforeseen 100x traffic spike degrades your service gracefully rather than causing a cascading failure.

### `02_Netflix_Scale: Event_Streaming_and_Personalization/`

- **The Viewing History Problem**: Storing 100 billion viewing events per day. Why a traditional RDBMS fails, why Cassandra works, and how to design the partition keys to avoid hot spots for popular shows.
- **Data Architectures for A/B Testing**: How to bucket 200 million users persistently, track their exposure to a feature, and join that exposure against petabytes of behavioral data in near real-time.

### `03_Amazon_Scale: Product_Catalog_and_Ordering/`

- **Saga Pattern for Distributed Transactions**: How Amazon handles an order checkout across Inventory, Payment, and Shipping microservices without a single global database lock.
- **Multi-Region Active-Active Data Replication**: Handling concurrent cart updates from different continents. Vector clocks, CRDTs (Conflict-free Replicated Data Types), and "last-write-wins" anomalies.

### `04_LinkedIn_Scale: Graph_Networks_and_The_Feed/`

- **The Activity Feed Architecture**: Fan-out-on-write (push) vs. Fan-in-on-read (pull). Dealing with the "Justin Bieber Problem" (super-nodes with 100M+ followers broadcasting an update).
- **Secondary Indexing at Petabyte Scale**: How to query "Find all Software Engineers in San Francisco who know React and are connected to John Doe" in under 50ms using scatter-gather patterns.

### `05_Uber_Scale: Real_Time_Geospatial_Analytics/`

- **Geohashing and S2 Cells**: Indexing the physical globe. Designing databases to efficiently answer "Which drivers are within a 2-mile radius of the rider right now?"
- **Lambda Architecture under SLA**: Streaming driver locations into memory for immediate ETA calculations, while simultaneously batching the same data to cold storage for machine learning route optimization.

### `06_Architecture_Decision_Records_ADR/`

- **Documenting the "Why"**: The absolute necessity of writing down the alternatives you *rejected* and why you rejected them.
- **Living with Technical Debt**: Designing the precise boundary interface where clean modern architecture connects to a legacy 20-year-old operational monolith.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
