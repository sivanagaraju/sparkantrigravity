# 🧠 Mind Map – Page Architecture

---

## How to Use This Mind Map
- **For Revision**: Review the page layout diagram and rows-per-page formula before any database internals interview
- **For Application**: Use the row width calculation to estimate storage and I/O for schema design decisions
- **For Interviews**: Be ready to draw a PostgreSQL 8KB page from memory and explain tuple headers
- **For Debugging**: Reference anti-patterns when investigating table bloat or slow scans

---

## 🗺️ Theory & Concepts

### The Page as the Unit of I/O
- Databases don't read individual rows — they read PAGES (fixed-size blocks)
  - PostgreSQL: 8KB (compile-time constant)
  - InnoDB: 16KB (configurable: 4/8/16/32/64KB)
  - SQL Server: 8KB (fixed)
  - Oracle: 2/4/8/16/32KB (configurable at tablespace level)
- Every query that touches disk reads at least one full page
  - Buffer pool caches recently-used pages in RAM
  - Buffer hit ratio: target > 95% for OLTP workloads

### PostgreSQL 8KB Page Layout
- Header (24 bytes): pd_lsn (WAL position), pd_checksum, pd_lower/pd_upper (free space boundaries)
- Line Pointers: 4-byte array growing DOWNWARD from header
  - Each entry: offset + length + flags for one tuple
  - Enables HOT (Heap-Only Tuple) optimization — update line pointer instead of creating index entry
- Free Space: gap between line pointers (growing down) and tuple data (growing up)
  - Free Space Map (FSM): separate file tracking available space per page
  - When page is full: FSM directs INSERTs to another page
- Tuple Data: grows UPWARD from bottom of page
  - Each tuple: 23-byte header + null bitmap + user data
  - Alignment: padded to 8-byte boundaries (MAXALIGN)

### Tuple Header (23 bytes) — MVCC Metadata
- t_xmin (4B): transaction ID that INSERT'd this row → visibility start
- t_xmax (4B): transaction ID that DELETE'd/UPDATE'd → visibility end (0 = live)
- t_cid (4B): command ID within transaction (for in-transaction visibility)
- t_ctid (6B): current tuple ID (block, offset) → points to next version after UPDATE
  - HOT chain: t_ctid of old version → new version on same page
- t_infomask (2+2+1B): status bits
  - HEAP_XMIN_COMMITTED: xmin is known committed (skip CLOG lookup)
  - HEAP_UPDATED: this tuple was created by UPDATE (not INSERT)

### InnoDB 16KB Page (Comparison)
- Records stored in PRIMARY KEY order (clustered index)
  - No separate heap — the B+ Tree leaf IS the data
- Page Directory: sparse index for binary search within page
  - PostgreSQL uses sequential scan within page (line pointers)
- Infimum/Supremum records: sentinel boundary records
- Double Write Buffer: protects against torn page writes

### TOAST (The Oversized-Attribute Storage Technique)
- Triggers when row exceeds ~2KB
- Large values moved to a separate TOAST table
  - Each fetch of a TOASTed column requires additional I/O
- Compression: PostgreSQL applies pglz or lz4 before TOASTing
- Strategies per column: PLAIN, EXTENDED, EXTERNAL, MAIN

---

## 🗺️ Techniques & Patterns

### T1: Rows-Per-Page Calculation
- Formula: `(page_size - header) / (tuple_header + null_bitmap + row_data + line_pointer + alignment)`
  - 8KB page, narrow row (50 bytes): ~120 rows/page
  - 8KB page, wide row (500 bytes): ~15 rows/page
  - 8KB page, very wide (2000 bytes): ~3 rows/page (+ TOAST for overflow)
- Impact: wide rows mean proportionally more pages, more I/O, less buffer pool efficiency
- Failure mode: VARCHAR(255) × 20 columns → 7 rows/page → 22x more I/O than necessary

### T2: Buffer Pool Sizing
- PostgreSQL: `shared_buffers` = 25% of RAM (official recommendation)
  - Example: 32GB RAM → 8GB shared_buffers → 1,048,576 pages cached
- `effective_cache_size` = 75% of RAM (tells planner about OS page cache)
- Monitor: `pg_statio_user_tables` → heap_blks_hit / (heap_blks_hit + heap_blks_read) > 0.95
- Failure mode: default 128MB on 200GB database → 65% hit ratio → every other query goes to disk

### T3: Page Split Prevention with fillfactor
- Default fillfactor = 100 → pages filled to 100%
- fillfactor = 70 → 30% headroom for future inserts
  - Reduces page splits (expensive: allocate + move + update parent + WAL)
  - Use for frequently-updated tables and indexes
- Failure mode: fillfactor=100 on write-heavy table → periodic latency spikes from page splits

### T4: Column Ordering for Alignment
- PostgreSQL aligns data types to their natural boundaries
  - INT8 (8 bytes) → 8-byte aligned
  - INT4 (4 bytes) → 4-byte aligned
  - INT2 (2 bytes) → 2-byte aligned
  - BOOL (1 byte) → no alignment
- Optimal: order columns from widest to narrowest to minimize padding waste
  - `(bigint, int, smallint, boolean)` → minimal padding
  - `(boolean, bigint, boolean, int)` → 7 bytes padding after each boolean

---

## 🗺️ Hands-On & Code

### Page Inspection
- `CREATE EXTENSION pageinspect;`
- `SELECT * FROM page_header(get_raw_page('table_name', 0));` → see pd_lower, pd_upper
- `SELECT lp, lp_off, t_xmin, t_xmax FROM heap_page_items(get_raw_page('table_name', 0));`

### Free Space Monitoring
- `CREATE EXTENSION pg_freespacemap;`
- `SELECT blkno, avail FROM pg_freespace('table_name');`

### Buffer Hit Ratio
- `SELECT sum(heap_blks_hit)::float / (sum(heap_blks_hit) + sum(heap_blks_read)) FROM pg_statio_user_tables;`

### TOAST Inspection
- `SELECT relname, pg_size_pretty(pg_relation_size(reltoastrelid)) FROM pg_class WHERE reltoastrelid != 0;`

---

## 🗺️ Real-World Scenarios

### 01: Stripe — Row Width Audit
- The Trap: VARCHAR(255) for 23 columns → 1,100 byte rows → 7 rows/page
- Scale: 12TB payments table, 85% buffer hit ratio
- The Fix: Right-sized columns → 200 byte rows → 38 rows/page → 4.2TB, 97% hit ratio

### 02: Instagram — TOAST Penalty
- The Trap: Bio text (2KB) + JSON metadata (5KB) in main profile table
- Scale: Profile lookups required 2 I/O (page + TOAST) instead of 1
- The Fix: Separated large columns → main table 180 bytes/row → p50 3ms → 0.8ms

### 03: Heroku — shared_buffers Misconfiguration
- The Trap: Default 128MB shared_buffers on 200GB database
- Scale: Buffer hit ratio 65%, every other query went to disk
- The Fix: 8GB shared_buffers → 96% hit ratio → p50 12ms → 2ms

### 04: Bloomberg — Page Splits
- The Trap: fillfactor=100 on write-heavy B-Tree indexes
- Scale: 50ms latency spikes every 2-3 minutes from page split contention
- The Fix: fillfactor=70 → spikes reduced to every 30+ minutes

---

## 🗺️ Mistakes & Anti-Patterns

### M01: VARCHAR(255) Default
- Root Cause: Schema design without data profiling
- Diagnostic: `pg_stats.avg_width` << declared column max across many columns
- Correction: Right-size to actual max + 20% margin; use UUID type for UUIDs

### M02: Ignoring Tuple Header Overhead
- Root Cause: Assuming column bytes = storage bytes
- Diagnostic: `pg_relation_size` >> (row_count × sum_of_column_widths)
- Correction: Account for 23B header + padding per tuple; denormalize for narrow-row access

### M03: Low Buffer Hit Ratio
- Root Cause: Default shared_buffers (128MB) on large database
- Diagnostic: `pg_statio_user_tables` hit ratio < 95%
- Correction: shared_buffers = 25% RAM; effective_cache_size = 75% RAM

### M04: BLOBs in Main Table
- Root Cause: Storing images/PDFs/large JSON directly in main table
- Diagnostic: `pg_relation_size(reltoastrelid)` > main table size
- Correction: Move large objects to separate table or S3; keep main table narrow

### M05: fillfactor=100 on Write-Heavy Tables
- Root Cause: Unaware of page split mechanics
- Diagnostic: Periodic latency spikes correlating with insert bursts
- Correction: fillfactor=70 for indexes, 90 for heap tables

---

## 🗺️ Interview Angle

### Core Knowledge Question
- "Describe the internal structure of a PostgreSQL page"
- Must include: header, line pointers, free space, tuples growing up, tuple header (xmin/xmax)

### Performance Diagnosis Question
- "Table is 10x larger than expected — what happened?"
- Check: dead tuples (VACUUM), TOAST, alignment padding, index bloat, over-wide columns

### I/O Estimation Question
- "Estimate I/O for a query on 1B rows"
- Formula: row_width → rows/page → total pages → scan time at disk throughput

### Design Impact Question
- "How does row width affect system performance?"
- Answer: rows/page ratio, buffer pool efficiency, scan I/O, TOAST threshold

---

## 🗺️ Assessment & Reflection
- Can you draw a PostgreSQL 8KB page layout from memory?
- Do you know the tuple header overhead for your production tables?
- Have you calculated rows-per-page for your most-queried tables?
- What is the buffer hit ratio on your production PostgreSQL instances?
- Have you audited for VARCHAR(255) → right-sized column opportunities?
- Do your write-heavy indexes use a reduced fillfactor?
