# 11 — Master Data Management (MDM) & Entity Resolution

> "Who is the customer? It sounds simple until you realize that Marketing, Sales, Finance, and Support each have a different definition, a different ID, and a different database."

MDM is the enterprise-scale problem of creating a single, authoritative "golden record" for core business entities (Customer, Product, Supplier, Employee, Location) across dozens of siloed systems. At FAANG scale, this means deduplicating billions of records with fuzzy matching algorithms.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_MDM_Architecture_Styles/`

- **Registry Style**: No data movement. A central registry maintains cross-references (Source A Customer #123 = Source B Customer #456). Fastest to implement, but no data cleansing.
- **Consolidation Style**: Data is copied into a central MDM hub, cleansed, and matched. The hub is the read-only golden record. Source systems are not updated.
- **Coexistence Style**: The MDM hub publishes the golden record back to source systems. Bi-directional sync. The most powerful and the most operationally nightmarish.
- **Centralized (Transactional) Style**: All creates/updates flow through the MDM hub first. The hub IS the system of record. Rare outside highly regulated industries (pharma, banking).

### `02_Entity_Resolution_Algorithms/`

- **Deterministic (Rule-Based) Matching**: Exact match on SSN, email, phone. Fast, but fails when data is dirty ("Jon Smith" vs. "Jonathan Smith", "123 Main St" vs. "123 Main Street").
- **Probabilistic (Fuzzy) Matching**: Jaro-Winkler distance, Levenshtein distance, Soundex, Metaphone. Assigning match scores and defining thresholds for auto-merge vs. human review.
- **Machine Learning Matching**: Training classifiers on labeled match/non-match pairs. Active learning: the system surfaces uncertain pairs for human labeling to improve the model iteratively.
- **Graph-Based Resolution**: Using transitive relationships. If Record A matches Record B (via email), and Record B matches Record C (via phone), then A, B, and C are likely the same entity — even though A and C share no common attributes.

### `03_The_Golden_Record/`

- **Survivorship Rules**: When merging 5 source records into 1 golden record, which source "wins" for each attribute? "Use CRM for name, use ERP for address, use the most recently updated phone number."
- **Trust Scores**: Assigning trustworthiness to each source system per attribute. The CRM has high trust for names but low trust for addresses. ERP is the opposite.
- **Hierarchy Management**: Modeling parent-child relationships (subsidiary → parent company → holding company). Handling mergers and acquisitions that restructure the hierarchy overnight.

### `04_Customer_360_Architecture/`

- **Building the Unified Customer View**: Stitching together web clickstream (anonymous cookie IDs), mobile app events (device IDs), CRM records (email), and transaction records (account numbers) into a single customer profile.
- **Identity Resolution at Scale**: Processing billions of interaction events to resolve anonymous visitors into known customers. Probabilistic identity graphs. The privacy implications (GDPR "right to be forgotten" for a record that exists in 14 different systems).
- **Real-Time vs. Batch Resolution**: Should the golden record update in real-time (complex, expensive) or in nightly batches (simpler, but stale data for intra-day use cases)?

---
*Part of [Principal Data Architect Learning Path](../README.md)*
