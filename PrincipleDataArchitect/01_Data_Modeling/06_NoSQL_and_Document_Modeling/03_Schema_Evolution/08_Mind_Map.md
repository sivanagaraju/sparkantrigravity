# 🧠 Mind Map – Schema Evolution

---

## How to Use This Mind Map

- **For Revision:** Scan the hierarchical headers and bullets to recall the full schema evolution lifecycle — from lazy migration through Expand-Contract — in 60 seconds.
- **For Application:** Before deploying a schema change, jump to **Techniques & Patterns** for the Expand-Contract protocol and the volume-based decision matrix.
- **For Interviews:** Use the **Interview Angle** branch to rehearse the "500 million documents" zero-downtime migration question.

---

## 🗺️ Theory & Concepts

### The Core Problem

- NoSQL databases have no `ALTER TABLE`
  - In relational: `ALTER TABLE ADD COLUMN` is a metadata-only operation (instant)
  - In document databases with 100M documents: there is no equivalent. Every document is independent
  - The application code IS the schema. When the code changes, old documents don't update themselves
- "Schemaless" Is a Myth
  - Every document has an implicit schema defined by the application code that reads/writes it
  - "Schemaless" means "multiple versions of the schema exist simultaneously"
  - The application must handle all versions. If it doesn't, it crashes on old documents

### Three Strategic Choices

- Lazy Migration (Update on Read)
  - When a document is read, check its version. If old, transform in memory and write back
  - Documents migrate gradually as users access them. Dormant documents stay in old format
  - No downtime required. No batch jobs. But code must handle ALL versions forever (until all docs migrate)
- Eager Migration (Batch Update)
  - Background script scans every document and updates to current version
  - Predictable completion time. After migration, the database is in a consistent state
  - Requires throttled workers to avoid overwhelming the database. Risk: long-running batch blocks other operations
- Application-Level Compatibility
  - Code handles both old and new formats. Old docs are left alone
  - Simplest for adding optional fields. Most dangerous for required fields (old docs lack the field)

### Who Formalized It

- Martin Fowler (2016): Evolutionary Database Design — incremental schema changes
- MongoDB: Schema Versioning Pattern — `schema_version` field in every document
- Event Sourcing Community: Event schema evolution — how to replay events written in old formats

### The Schema Versioning Pattern

- Add a `schema_version: INT` field to every document
- DAO layer checks the version and routes to the appropriate migration function
- Migration functions are chained: `v1_to_v2()`, `v2_to_v3()`, etc.
- New writes always use the latest version. Old documents migrate on read (lazy) or via batch (eager)

---

## 🗺️ Techniques & Patterns

### T1: Lazy Migration (Update on Read)

- When to use: High-volume collections (>100M docs) where batch migration is too slow or risky
- Step-by-Step Protocol
  - 1. Read document
  - 1. Check `schema_version` field (or detect field presence for implicit versioning)
  - 1. If version < current: apply transformation chain (v1 → v2 → v3)
  - 1. Write updated document back with new `schema_version`
  - 1. Code MUST handle all old versions gracefully until 100% migration
- Decision Heuristic
  - Use when: zero-downtime requirement, 100M+ docs, gradual rollout acceptable
  - Avoid when: field is required for queries (old docs won't have it, breaking query predicates)
- Failure Mode
  - Dormant documents never get read, never migrate. Discovery: Run a count query on `schema_version < current`
  - Fix: Combine with targeted backfill for documents not accessed in 90+ days

### T2: Eager Migration (Batch Update)

- When to use: Small-to-medium collections (<1M docs) or when consistent state is required for analytics/BI
- Step-by-Step Protocol
  - 1. Write migration script (scan all docs, apply transformation, update in place)
  - 1. Throttle writes (e.g., 500 docs/second) to avoid overwhelming the database
  - 1. Monitor progress: log percentage complete, track errors
  - 1. Verify: run count query to confirm 0 documents remain at old version
  - 1. Deploy code that assumes new schema (can remove old-version handling)
- Decision Heuristic
  - Use when: <1M docs, scheduled maintenance window available, or analytics needs consistent schema
  - Avoid when: >100M docs (too slow), zero-downtime requirement (batch may cause throttling)
- Failure Mode
  - Batch job crashes mid-run. Half the documents are v2, half are v1
  - Fix: Make migration idempotent. Re-running on an already-migrated doc should be a no-op

### T3: Expand-Contract Pattern (Zero-Downtime, Any Scale)

- When to use: Mission-critical systems that require zero-downtime AND consistent state
- Phase 1: Expand
  - Add the new field alongside the old field
  - Dual-write: Write to BOTH old and new fields on every write
  - Read: Use new field if present, fallback to old field
  - Duration: Until all running application versions support the new field
- Phase 2: Backfill
  - Batch process all existing documents to populate the new field from old field data
  - Verify: 100% of documents have the new field populated
  - At this point, all reads are served from the new field (old field is redundant)
- Phase 3: Contract
  - Remove old code paths (stop reading/writing old field)
  - Remove old field from documents (`$unset` in MongoDB)
  - Enforce strict JSON Schema validation requiring the new field
  - Duration: Cleanup sprint — can be deferred if low priority
- Failure Mode
  - Skipping Phase 2: New field exists in new documents but old documents still lack it. Queries on new field return incomplete results
  - Skipping Phase 3: Dead code paths and ghost fields accumulate indefinitely. Schema debt compounds

### T4: Implicit Versioning (Detect Field Presence)

- When to use: Quick, informal changes where adding a `schema_version` field is overkill
- Mechanics
  - Instead of checking `schema_version`, detect field presence: `if "new_field" in doc: use new_field else: compute from old_field`
  - Works for simple additions. Breaks for renames or type changes (can't distinguish missing vs null)
- Failure Mode
  - Ambiguity: Is the field missing because it's an old doc, or because the user intentionally omitted it?
  - Fix: If you have more than 2 versions, switch to explicit `schema_version`

### Volume-Based Decision Matrix

- <1M docs: EAGER migration (fast, simple, predictable)
- 1M - 100M docs: LAZY + targeted backfill for dormant documents
- >100M docs: LAZY only. Eager is too slow and risks throttling
- Mission-critical / zero-downtime: EXPAND-CONTRACT (regardless of volume)
- Analytics/BI dependency: EAGER (analytics needs consistent schema, not mixed versions)

---

## 🗺️ Hands-On & Code

### Python SchemaAdaptor Pattern

- Base class: `SchemaAdaptor` with `migrate(doc)` method
- Version-specific subclasses: `V1ToV2Adaptor`, `V2ToV3Adaptor`
- DAO layer: `doc = adaptor_chain.migrate(raw_doc)` before returning to application
- Chain pattern: `v1_to_v2(v2_to_v3(doc))` — composable, testable, idempotent

### MongoDB Operations

- Eager: `db.collection.updateMany({schema_version: {$lt: 3}}, [{$set: {new_field: {$ifNull: ["$old_field", "default"]}, schema_version: 3}}])`
- Contract: `db.collection.updateMany({}, {$unset: {old_field: ""}})`
- Validation: `db.runCommand({collMod: "collection", validator: {$jsonSchema: {...}}})`

### JSON Schema Validation

- MongoDB supports built-in JSON Schema enforcement
- "Warn" mode: Log invalid writes but don't reject (use during transition)
- "Error" mode: Reject invalid writes at DB level (use after Contract phase)
- Purpose: Prevent regressions — new code can't write old-format documents

### Tooling Integration

- Schema Registry (Confluent / Glue): Enforce Avro/Protobuf compatibility rules
  - BACKWARD: New schema can read old data
  - FORWARD: Old schema can read new data
  - FULL: Both directions (safest for streaming)
- Change Streams: Trigger downstream sync when documents mutate
  - Use for: Keeping denormalized views consistent after schema migration

---

## 🗺️ Real-World Scenarios

### 01: Netflix — Lazy Migration for Playback Records

- Scale: Hundreds of millions of user profiles, billions of playback records
- The Setup: New "playback quality" field needed for ML recommendations
- Design: Lazy migration. On read: if `schema_version < 2`, compute `playback_quality` from existing `bitrate` and `resolution` fields, write back
- Duration: 6 months for 95% migration. Remaining 5% were dormant users — backfilled via batch
- Key Learning: Lazy works but you MUST pair it with a dormant-document backfill strategy

### 02: E-Commerce Platform — Expand-Contract for Address Restructuring

- Scale: 50M customer documents
- The Setup: Flatten `{address: {line1, line2, city, state, zip}}` to top-level fields `{address_line1, address_city, ...}`
- Phase 1 (Expand): Dual-write both formats for 2 sprints
- Phase 2 (Backfill): Batch migration of 50M docs over 3 days (throttled at 1,000 docs/sec)
- Phase 3 (Contract): Removed nested `address` field, enforced JSON Schema requiring flat fields
- Key Learning: The 3-phase approach prevented any downtime and caught 12 edge cases during dual-write

### Post-Mortem: Multi-Version Collision

- The Trap: Two application versions running simultaneously during rolling deploy
  - App v1 writes `{price: "19.99"}` (string)
  - App v2 writes `{price: 19.99}` (number)
- What Broke: Aggregation pipeline crashed on `$sum` — can't sum strings and numbers
- Root Cause: No `schema_version` field. No Expand-Contract. Both versions wrote to the same field with different types
- The Fix: Added `schema_version` to all documents. Eager migration to convert all string prices to numbers. Added JSON Schema validation rejecting string prices
- Lesson: Rolling deploys with schema changes REQUIRE either Expand-Contract or explicit versioning. Implicit "just change the type" causes data corruption

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Assuming NoSQL Is Schemaless

- Root Cause: "MongoDB is schemaless, so we don't need to think about schema changes"
- Diagnostic: Application crashes on NoneType when accessing a field that doesn't exist in old documents
- Correction: Every document has an implicit schema. Manage it explicitly with `schema_version` and migration functions

### M02: Big-Bang Eager Migration on 100M+ Docs

- Root Cause: Running an unthrottled `updateMany` on a massive collection during business hours
- Diagnostic: Database throughput drops 80%. Application requests timeout
- Correction: Throttle to 500-1,000 docs/second. Run during off-peak hours. Or use Lazy Migration instead

### M03: Skipping the Contract Phase

- Root Cause: Expand and Backfill done, but old fields and code paths are never cleaned up
- Diagnostic: Codebase has `if "old_field" in doc` checks from 3 years ago. Schema debt compounds
- Correction: Schedule a "Contract Sprint" after every Expand-Contract migration. Remove dead code and ghost fields

### M04: No Idempotent Migration Functions

- Root Cause: Migration script fails mid-run. Restarting it re-migrates already-migrated documents
- Diagnostic: Field values are doubled, concatenated, or corrupted after re-run
- Correction: Always check: `if doc.schema_version >= target: return doc unchanged`. Migration MUST be a no-op on already-migrated docs

### M05: Changing Field Types Without Expand-Contract

- Root Cause: Renaming `price` from string to number in a rolling deploy. Both types coexist
- Diagnostic: Aggregation pipelines crash. Query filters return unexpected results
- Correction: NEVER change a field type in place. Use Expand-Contract: add `price_v2` (number), backfill, remove `price` (string)

---

## 🗺️ Interview Angle

### Q1: Add a Mandatory Field to 500M Documents Without Downtime

- What They Test: Do you know Expand-Contract?
- Principal Answer: Phase 1 (Expand): Add new field, dual-write. Phase 2 (Backfill): Batch-update 500M docs (throttled, 3-7 days). Phase 3 (Contract): Remove old field, enforce validation
- Follow-Up Trap: "What if the backfill takes too long?" → Lazy migration for the long tail. Combine: Eager for hot documents, Lazy for cold

### Q2: How Do You Handle Rolling Deploys with Schema Changes?

- What They Test: Do you understand the multi-version problem?
- Principal Answer: During a rolling deploy, App v1 and App v2 run simultaneously. Both must be able to read/write the same documents. Solution: Expand-Contract ensures backward AND forward compatibility during the transition window

### Q3: Lazy vs Eager — When Do You Choose Each?

- What They Test: Do you have a decision framework?
- Principal Answer: Volume-based matrix: <1M → Eager, >100M → Lazy, Mission-critical → Expand-Contract. Plus: If the field is required for queries (e.g., indexed field), Lazy won't work — use Eager to ensure 100% population

### Whiteboard Blueprint

- The "3-Phase Migration Timeline": Expand (dual-write) → Backfill (batch) → Contract (cleanup)
- Draw the document state at each phase showing which fields exist and which app versions can read/write

---

## 🗺️ Assessment & Reflection

- Do your documents have a `schema_version` field? If not, how do you detect which version they are?
- How many schema versions currently coexist in your production database?
- Is there dead Expand-phase code in your codebase that was never Contracted?
- Are your migration functions idempotent? What happens if you re-run them?
- Do you have JSON Schema validation enabled? In "warn" or "error" mode?
