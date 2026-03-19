# 🧠 Mind Map — Time-Series Databases (TSDB)

---

## How to Use This Mind Map
- **For Revision**: Review the Theory, Storage, and Pitfalls sections to refresh your fundamental understanding.
- **For Application**: Use the Evaluation & Tooling section to select the right engine (Timescale vs. Influx vs. ClickHouse).
- **For Interviews**: Rehearse the Cardinality and Compression (Gorilla) talking points for Principal-level design sessions.

---

## 🗺️ Theory & Core Concepts

### Temporal Data Profile
- **Append-Only**
  - Data is written chronologically and almost never updated.
- **High Volume**
  - Sustaining 100k to 1M+ inserts per second.
- **Time-Range Queries**
  - Almost all reads filter by a specific time window.
- **Data Aging (TTL)**
  - Value of individual points decreases over time; importance of trends increases.

### Key Dimensions
- **Metric Name**: The qualitative measurement (e.g., `cpu_usage`).
- **Tags / Labels**: Indexed metadata (e.g., `host_id`, `region`, `app_version`).
- **Fields / Samples**: The raw numeric measurement values (floats/integers).
- **Timestamp**: The temporal coordinate of the event.

---

## 🗺️ Storage & Compression Mechanics

### Engine Internals
- **WAL (Write Ahead Log)**
  - Ensures durability before in-memory buffering.
- **Inverted Index**
  - Maps tag values to Series IDs for $O(1)$ series identification.
- **MemTable / Cache**
  - Holds the most recent data "Head" for instant querying.
- **TSM / SSTables**
  - Immutable, sorted data files on disk for long-term storage.

### Data Compression (Gorilla Algorithm)
- **Delta-Delta Encoding**
  - Stores only the difference between timestamps, saving massive space for steady rhythms.
- **XOR Compression**
  - Stores XOR of current float with previous float; similar values result in many leading zeros.
- **Impact**
  - Typically achieves 10:1 or 20:1 storage reduction on raw data.

---

## 🗺️ Techniques & Patterns

### T1: Hierarchical Downsampling
- **Purpose**: Balance storage cost vs. historical visibility.
- **Pattern**
  - Keep 1s raw data for 7 days.
  - Automate 1m rollups (mean/max) for 90 days.
  - Automate 1h rollups for 3 years.

### T2: Partitioning (Hypertables)
- **Mechanism**: Automatically dividing a single logical table into physical time-based chunks.
- **Benefit**: Keeps indexes small enough to fit in RAM; makes "dropping" old data (TTL) a metadata operation rather than a slow `DELETE` query.

### T3: ASOF Joins
- **Requirement**: Finding the record with the closest timestamp *before* a target event.
- **Scenario**: In HFT (High-Frequency Trading), joining a trade with the prevailing quote at that exact millisecond.

---

## 🗺️ Real-World Case Studies

### 01: Facebook Gorilla
- **Success**: Reduced metric size from 16 bytes to 1.37 bytes.
- **Architecture**: In-memory-first engine for millisecond dashboard refreshes.

### 02: Uber M3
- **Challenge**: Scale to 500 million metrics per second across global data centers.
- **Fixed logic**: Created a decentralized hash ring and integrated natively with Prometheus PromQL.

### 03: Netflix Atlas
- **Philosophy**: Observability is a RAM problem, not a disk problem. 
- **Design**: Keeps high-resolution "Head" data in large memory clusters; exports "Cold" data to S3.

---

## 🗺️ Pitfalls & Anti-Patterns

### M01: Cardinality Explosion
- **Root Cause**: Putting high-unique values (IDs, GUIDs, IPs) into Tags/Labels.
- **Outcome**: Index grows too large for RAM → Ingestion stalls → Database OOMs.

### M02: Massive Batching (Lag)
- **Root Cause**: Waiting too long (e.g., 5 min) to push data to the server.
- **Outcome**: "Last-Value" queries on dashboards show empty data; Prometheus lookback windows fail.

### M03: Text in TSDB
- **Root Cause**: Storing log messages or error strings in field values.
- **Outcome**: Compression fails; Disk I/O spikes. Use Elastic/Loki instead.

---

## 🗺️ Evaluation & Tooling

### Engine Selection
- **TimescaleDB**: If you already use Postgres and need SQL power.
- **InfluxDB**: If you need a custom-built, push-based metrics engine.
- **Prometheus**: If you need a pull-based, cloud-native monitoring standard.
- **ClickHouse**: If you need high-speed OLAP over massive event streams.
- **VictoriaMetrics**: If you want a high-performance, cost-effective Prometheus backend.

---

## 🗺️ Assessment & Reflection
- [ ] Could you explain the difference between a Tag and a Field?
- [ ] Can you describe how XOR compression works to an interviewer?
- [ ] Do you know how to calculate the cardinality of your current production metrics?
- [ ] **Audit Question**: Are you storing `user_id` as a tag in any Prometheus metric? (If yes, fix it!)
