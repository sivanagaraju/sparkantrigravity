# Schema Evolution — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Big-Bang Schema Change (No Expand Phase)

**The mistake**: Deploying a new application version that writes documents in a new format without maintaining backward compatibility with existing documents.

**What breaks**: The new code expects new field names/types. Existing documents have old field names/types. Any read of an existing document causes a runtime error (TypeError, KeyError, null pointer).

**Detection**:

- Spike in application errors immediately after deployment
- Error messages referencing missing fields or type mismatches

**Fix**: Always use the expand-contract pattern:

1. **Expand**: New code reads both old and new format. Writes in new format.
2. **Backfill**: Batch migrate old documents to new format.
3. **Contract**: After 100% migration, remove old-format handling code.

---

## Anti-Pattern 2: No Schema Version Field

**The mistake**: Not including a `schema_version` field in documents. Without it, the application must infer the version from field presence/absence — fragile and error-prone.

**Detection**:

```javascript
// Check if documents have schema versioning
db.users.aggregate([
  { $group: {
      _id: { $ifNull: ["$schema_version", "MISSING"] },
      count: { $sum: 1 }
  }},
  { $sort: { count: -1 } }
]);
// If "MISSING" is the majority, versioning was never implemented.
```

**Fix**: Add `schema_version` to all documents:

```python
# Add version to all existing documents (one-time backfill)
users.update_many(
    {'schema_version': {'$exists': False}},
    {'$set': {'schema_version': 1}}
)
# All new writes include schema_version
```

---

## Anti-Pattern 3: Eager Migration Without Throttling

**The mistake**: Running a batch migration that updates 100M documents at full speed, saturating the database's I/O and causing latency spikes for production traffic.

**What breaks**: MongoDB's WiredTiger engine handles concurrent reads/writes, but a batch job doing 50K writes/second competes with production traffic for I/O, locks, and cache. Result: production P99 latency jumps from 10ms to 500ms during migration.

**Detection**: Correlate production latency spikes with batch job execution times.

**Fix**: Throttle the migration:

```python
import time

def throttled_migration(batch_size=500, sleep_seconds=0.5):
    """Migrate in small batches with pauses to minimize production impact."""
    while True:
        # Process one batch
        docs = list(users.find(
            {'schema_version': 1},
            limit=batch_size
        ))
        
        if not docs:
            break  # All migrated
        
        ops = [UpdateOne({'_id': d['_id']}, {'$set': migrate_v1_to_v2(d)}) 
               for d in docs]
        users.bulk_write(ops, ordered=False)
        
        # Pause to let production traffic breathe
        time.sleep(sleep_seconds)
```

---

## Anti-Pattern 4: Ignoring Forward Compatibility

**The mistake**: Planning only for backward compatibility (new code reads old docs) but not forward compatibility (old code reads new docs).

**What breaks during rolling deployment**: During a rolling update, some pods run v1 and some run v2. A v2 pod writes a document with new fields. A v1 pod reads it — and crashes because it encounters unexpected fields or types.

**Fix**: Design for both directions:

- **Backward**: New code handles missing fields with defaults
- **Forward**: Old code ignores unknown fields (don't fail on extra fields)

```python
# BACKWARD compatible: handle missing field
email_verified = doc.get('email_verified', False)  # default if missing

# FORWARD compatible: don't fail on unknown fields
# In Python: dict access is naturally tolerant of extra keys
# In TypeScript/Java: define schemas with additionalProperties: true
```

---

## Anti-Pattern 5: Not Cleaning Up Old Fields After Migration

**The mistake**: Completing the expand and backfill phases but never running the contract phase. Old fields accumulate in documents, wasting storage and confusing future developers.

**Detection**:

```javascript
// Find documents with deprecated fields still present
db.users.countDocuments({ 'name': { $exists: true } });
// If count > 0 but 'name' was deprecated 6 months ago, cleanup is overdue.
```

**Fix**: Schedule the contract phase as a tracked engineering task:

```python
# Cleanup old fields — run ONLY after 100% migration verified
users.update_many(
    {'name': {'$exists': True}},
    {'$unset': {'name': '', 'legacy_field': '', 'old_status': ''}}
)
```

---

## Decision Matrix — Common Migration Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| No expand phase | Production crash on deploy | Schema evolution checklist in PR review |
| No schema_version | Can't track migration progress | Mandatory field in document creation |
| Unthrottled batch | Production latency spike | Throttled batch with sleep intervals |
| No forward compat | Crash during rolling deploys | Test both v1→v2 and v2→v1 reads |
| No contract cleanup | Storage waste, developer confusion | Post-migration cleanup task in backlog |
