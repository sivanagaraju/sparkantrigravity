# 🧠 Mind Map – Query-Driven Modeling

---

## How to Use This Mind Map

- **For Revision:** Scan the hierarchical headers and bullets to recall the entire concept — from access pattern enumeration through DynamoDB key design — in 60 seconds.
- **For Application:** Before designing a new NoSQL data model, jump to **Techniques & Patterns** for the step-by-step workflow and partition key heuristics.
- **For Interviews:** Use the **Interview Angle** branch to rehearse the social media feed design question and the Scan vs Query cost explanation.

---

## 🗺️ Theory & Concepts

### Foundational Philosophy

- Access Patterns First
  - Enumerate every API endpoint before touching the DDL
  - Define filters (query parameters), projections (returned fields), and latency targets (P99 <10ms)
  - The model IS the query. If you can't name the query, you can't design the table
- Storage vs Compute Trade-off
  - Relational: Normalize to save storage. Use compute (CPU) for JOINs at read time
  - NoSQL: Denormalize to save compute. Use storage (disk) to pre-join data at write time
  - At web scale (>100K reads/sec), compute is the bottleneck. Storage is cheap
- Predictable Scaling
  - Partition-key lookups are O(1) regardless of table size
  - No JOINs = no N+1 queries = no surprise latency at 10x traffic
  - Amazon DynamoDB: 50M+ requests/second at <10ms P99

### Who Formalized It

- Rick Houlihan (AWS)
  - Popularized single-table design for DynamoDB
  - "One table to rule them all" — multiple entity types, differentiated by PK/SK prefixes
- MongoDB Documentation
  - "Model data for your application's queries" — explicit query-first guidance
- Apache Cassandra Guidelines
  - One table per query pattern — write amplification accepted as a design trade-off

### Key Terminology

- Access Pattern: A specific read or write operation the app performs
- Partition Key (PK): Distributes data across physical nodes. Same PK = same partition
- Sort Key (SK / Clustering Column): Orders items within a partition. Enables range queries
- Single-Table Design: All entity types in one DynamoDB table, differentiated by PK/SK prefixes
- Denormalization: Deliberately duplicating data so each read is served without JOINs
- Write Amplification: Cost of denormalization — one logical update writes to multiple items/tables
- Hot Partition: A partition receiving disproportionate traffic due to low-cardinality or skewed PK
- GSI (Global Secondary Index): Alternate partition key on the same table — enables different access patterns
- Scatter-Gather: Querying multiple partitions and combining results — defeats the purpose of PK design

---

## 🗺️ Techniques & Patterns

### T1: Access Pattern Enumeration

- When to use: Before any DDL, before any code
- Step-by-Step Protocol
  - 1. List every API endpoint the application exposes
  - 1. For each endpoint: identify the query predicate (filter), sort order, and projected fields
  - 1. Assign a latency SLA (e.g., <5ms for GetItem, <10ms for Query)
  - 1. Classify as Read or Write, and estimate QPS
  - 1. Document in an Access Pattern Table (AP#, Pattern, Operation, PK, SK, Index, Latency SLA)
- Failure Mode
  - Discovering a missing access pattern in production. Fix requires new GSI or table redesign
  - Prevention: The AP Table is a contract between architect, developer, and product manager

### T2: Partition Key Design

- When to use: After access patterns are enumerated
- Decision Heuristics
  - High Cardinality: PK must have millions of distinct values (user_id, order_id, sensor_id)
  - Even Distribution: No single PK value should receive >1% of total traffic
  - If a natural PK has low cardinality (status, date, country), use a composite key or GSI
- DynamoDB Specifics
  - Per-partition limit: 3,000 RCU, 1,000 WCU
  - If one PK exceeds this, you get ProvisionedThroughputExceededException
- Failure Mode
  - Date-based PK (e.g., `SENSOR#2024-03-15`) — all data for one day lands in one partition
  - Celebrity/hot-user PK — one user generates 80% of traffic

### T3: Sort Key Design

- When to use: When items within a partition need ordering or hierarchical grouping
- Patterns
  - Hierarchical: `USER#123 / ORDER#ts` — profile + order history in one partition
  - Time-series: `PREFIX#YYYY-MM-DD` — enables range scans within time windows
  - Entity overloading: SK = `PROFILE`, `ORDER#ts`, `FOLLOWER#id` — multiple entity types in one partition
- Failure Mode
  - Unbounded sort key growth: A channel with 5 years of messages has millions of items in one partition
  - Fix: Time-bucket the PK (e.g., `CHANNEL#id#2024-03`)

### T4: Denormalization Strategies

- When to use: When reads must be served from a single partition lookup
- Pre-Joining
  - Store related entities in the same partition (user + orders + addresses)
  - Trade-off: Write path becomes more complex (must update multiple items on entity change)
- Data Duplication
  - Write the same data to multiple views (e.g., order stored under both customer and status partitions)
  - Trade-off: Write amplification. Netflix writes each view event to 5+ tables
- Pre-Computed Aggregates
  - Store counts, sums, averages in the parent entity. Update via background job or DynamoDB Streams
- Failure Mode
  - Forgetting to update ALL copies when source data changes
  - Result: Stale data in denormalized views. Detection: Compare source vs copy in batch audit

### T5: GSI Strategy

- When to use: When an access pattern needs a different partition key than the base table
- DynamoDB GSIs
  - GSI has its own PK/SK — a fully separate partition structure
  - Reads from GSI are eventually consistent (not strongly consistent)
  - Each GSI adds write cost (every table write replicates to each GSI)
- Heuristic
  - 1-2 GSIs: Normal. 3: Review if needed. 4+: Probably over-indexed
  - Each GSI costs ~1x additional write capacity
- Failure Mode
  - GSI Fatigue: 5+ GSIs slow down every write. Storage cost explodes

---

## 🗺️ Hands-On & Code

### DynamoDB Single-Table DDL

- PK: `USER#<id>`, `ORDER#<id>`, `PRODUCT#<id>` (entity type prefixed)
- SK: `PROFILE`, `ORDER#<timestamp>`, `ITEM#<seq>`, `METADATA`
- GSI1PK: `email` (for user-by-email lookup)
- GSI2PK: `STATUS#PENDING` (for status-based queries)
- Table creation via `boto3.client('dynamodb').create_table()`

### Cassandra One-Table-Per-Query DDL

- `users_by_id`: PK = `user_id` — direct lookup
- `users_by_email`: PK = `email` — different partitioning for email search
- `orders_by_customer`: PK = `customer_id`, Clustering = `order_date DESC` — sorted by date
- Key principle: Same data, different physical tables, different partition keys

### MongoDB Document Design

- Compound indexes: `{email: 1}`, `{"address.city": 1, created_at: -1}`
- Embedding recent orders in user document (subset pattern)
- Aggregation pipeline for analytics; primary reads are point lookups

### Integration Architecture

- API Gateway → Lambda/ECS → Data Access Layer → DAX (cache <1ms) → DynamoDB
- CDC path: DynamoDB Streams → Kinesis Firehose → S3 (Parquet) → Glue Catalog → Athena (ad-hoc SQL)
- Principle: Separate operational (<10ms) and analytical (seconds) workloads via CDC

---

## 🗺️ Real-World Scenarios

### 01: Amazon — DynamoDB Single-Table for Retail

- Scale: 50M+ requests/second at peak (Prime Day)
- Architecture: Single-table per bounded context
  - Shopping Cart: PK=`CART#<customerId>`, SK=`ITEM#<productId>`. One query returns entire cart
  - Order History: PK=`CUSTOMER#<id>`, SK=`ORDER#<timestamp>`. Newest-first is one query
- Key Design: Tables treated as materialized API contracts. Each GSI maps 1:1 to an API endpoint

### 02: Netflix — Cassandra for Personalization

- Scale: 230M+ subscribers, 100B+ viewing events, 3,000+ Cassandra nodes across 3 regions
- Architecture: One table per access pattern
  - `user_viewing_history`: PK=`user_id`, SK=`watch_date DESC`
  - `similar_titles`: PK=`title_id`, SK=`similarity_score DESC`
- Key Trade-off: Massive write amplification (each view writes to 5+ tables) for single-partition read

### 03: Uber — DynamoDB for Trip Data

- Scale: 25M+ trips/day, real-time update latency <10ms
- Architecture: PK=`TRIP#<tripId>` for real-time, PK=`RIDER#<riderId>` for history
- Key Learning: Different PKs for different consumers of the same data

### 04: Discord — Cassandra for Message Storage

- Scale: 150M+ MAU, 4B+ messages/day, trillions of total messages
- Architecture: Time-bucketed partitions (PK = `channel_id + daily_bucket`)
- Key Design: Without bucketing, active channels would blow past the 100MB partition limit

### Post-Mortem: Hot Partition (IoT Platform)

- The Trap: PK = `sensor_date` (e.g., `SENSOR#2024-03-15`). All 100K sensors write to one partition
- Timeline: Month 0 fine → Month 6 continuous ProvisionedThroughputExceededException → 30% writes rejected
- Root Cause: PK cardinality = 1 per day. Per-partition limit = 1,000 WCU. Need = 100,000 WCU
- The Fix: Changed PK to `sensor_id`. Added GSI with PK=`date` for date-based queries
- Lesson: Partition keys must have high cardinality AND even distribution

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Normalizing in NoSQL (Relational Thinking)

- Root Cause: Designing DynamoDB/Cassandra as if relational — separate tables with FK references
- Diagnostic: Count the number of round trips per API call. If >1, you're normalizing
- Correction: Denormalize into a single table. One query = one partition = one round trip

### M02: Low-Cardinality Partition Keys

- Root Cause: Using `status`, `date`, or `country` as PK. All traffic concentrates on 3-5 partitions
- Diagnostic: CloudWatch `ConsumedReadCapacityUnits` spikes on specific partitions
- Correction: Use high-cardinality PK (entity_id). Move low-cardinality queries to GSI

### M03: Scan Instead of Query

- Root Cause: Using `table.scan(FilterExpression=...)` to find items
- Diagnostic: Scan reads EVERY item, then filters. Cost = O(n). 100M items at 1KB = 25M RCU per Scan
- Correction: Add a GSI where PK matches the query predicate. Turns O(n) into O(result_size)

### M04: Unbounded Partition Growth

- Root Cause: PK = `channel_id` for messages. Partition grows from KB to GB over years
- Diagnostic: Cassandra partitions >100MB degrade read performance. DynamoDB item collections >10GB hit limit
- Correction: Time-bucket the PK: `channel_id#2024-03`. "Load channel" queries current bucket only

### M05: No Access Pattern Document

- Root Cause: Writing code before enumerating access patterns. Discover missing AP in production
- Diagnostic: "We need a new query" results in a GSI addition or table redesign
- Correction: Create AP Table before any code. It is the contract between architect, developer, and PM

---

## 🗺️ Interview Angle

### Q1: Design DynamoDB for Social Media Feed

- What They Test: Do you start with access patterns, not entities?
- Principal Answer: Enumerate 6 APs (profile, posts, post detail, followers, follow check, feed) → map to PK/SK → identify fan-out trade-off for celebrity users
- Follow-Up Trap: "What about celebrities with 10M followers?" → Hybrid: fan-out-on-write for normal users, fan-out-on-read for celebrities

### Q2: What's Wrong with DynamoDB Scan?

- What They Test: Do you understand the cost model?
- Principal Answer: Scan cost = total_items × item_size / 4KB, regardless of filter. Fix = add GSI with PK matching the predicate
- Follow-Up Trap: "What about parallel Scan?" → Faster but still O(n) cost. Only for batch, never for online

### Q3: When NOT to Use Query-Driven Modeling?

- What They Test: Can you identify the boundaries of your expertise?
- Principal Answer: Three failure cases: unknown access patterns (use warehouse), rapidly changing APs (use relational), complex cross-entity queries (use relational)
- Decision Framework: If you can enumerate APs on a whiteboard and they're stable 6+ months → query-driven. If not → PostgreSQL

### Q4: Ad-Hoc Analytics with DynamoDB?

- What They Test: Do you know to separate OLTP and OLAP?
- Principal Answer: DynamoDB Streams → Kinesis Firehose → S3 (Parquet) → Athena for SQL. Never query DynamoDB directly for analytics

### Whiteboard Blueprint

- The "Access Pattern to Key Mapping" diagram: Box of APs on the left → arrows to a single DynamoDB table with PK/SK rows → GSI boxes for alternate access patterns
- Must draw in under 5 minutes. Focus on PK/SK overloading, not on infrastructure

---

## 🗺️ Assessment & Reflection

- Can you enumerate all access patterns for your current project and map them to PK/SK?
- Are any of your NoSQL queries doing Scatter-Gather (multiple partition reads)?
- How many GSIs do your tables have? Is each one justified by a distinct access pattern?
- Have you ever hit a Hot Partition? What was the PK cardinality?
- Is your Access Pattern Document up to date, or does it only exist in someone's head?
