# MySQL InnoDB — Concept Overview

> The clustered index engine: where the primary key IS the table.

## InnoDB Key Difference from PostgreSQL

```
PostgreSQL: Heap (unordered rows) + separate B-Tree indexes pointing to heap
InnoDB:     Clustered B+ Tree (rows stored IN the primary key index)
            Secondary indexes → primary key → row
```

**Consequence**: InnoDB range scans on PK are blazing fast (data is physically ordered). But secondary index lookups require a double lookup (secondary → PK → data).

## Buffer Pool vs Shared Buffers

| Feature | InnoDB Buffer Pool | PostgreSQL Shared Buffers |
|---|---|---|
| **Default** | 128MB (should be 70-80% of RAM) | 128MB (should be 25% of RAM) |
| **Page Size** | 16KB | 8KB |
| **Change Buffer** | ✅ Defers secondary index writes | ❌ |
| **Adaptive Hash Index** | ✅ Auto-builds hash for hot pages | ❌ |
| **Double Write Buffer** | ✅ Crash safety for partial writes | ❌ (full-page writes in WAL) |

## References

| Resource | Link |
|---|---|
| [InnoDB Architecture](https://dev.mysql.com/doc/refman/8.0/en/innodb-architecture.html) | Official docs |
| *High Performance MySQL* 4th Ed. | Silvia Botros & Jeremy Tinley |
