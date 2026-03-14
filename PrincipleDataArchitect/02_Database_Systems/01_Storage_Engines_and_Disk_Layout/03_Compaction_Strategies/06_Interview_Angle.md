# Compaction Strategies — Interview Angle

---

## Application in Architecture Interviews

Compaction strategy questions are a proxy for testing your understanding of distributed database mechanics, specifically how to navigate the **RUM Conjecture** (Read vs. Update vs. Memory/Space). Interviewers use this to see if you can configure systems like Cassandra or RocksDB correctly for different workloads.

---

## Sample Questions

### Q1: "You notice your SSDs on your database cluster are burning out and wearing down aggressively every ~6 months. What is likely happening and how do you fix it?"

**What they're testing**: Knowledge of Write Amplification (WA) and its relationship to compaction levels.

**Weak Answer**: "I would optimize my writes, batch them together, or buy hardier enterprise SSDs."
→ *Why it's weak*: It ignores the architectural root cause entirely (LSM tree configuration).

**Strong (Principal) Answer**: "The root cause is aggressive Write Amplification, likely because we are using an LSM database (like RocksDB or Cassandra) configured with **Leveled Compaction Strategy (LCS)** on a write-heavy workload. LCS strictly partitions data into overlapping levels, meaning a single piece of inserted data might be rewritten physically 10 to 30 times as it is pushed down the cascade into deeper levels to clear L0 for new writes. 

To fix this, I would measure the Write Amplification ratio, verify the workload is write-heavy rather than read-heavy, and switch the compaction strategy to **Size-Tiered (STCS)** or Universal compaction. This allows files to group naturally without aggressive downward merging, dropping write amplification to ~3x or 4x, immediately saving the SSD lifetime at the acceptable cost of slightly slower reads."

---

### Q2: "A Cassandra table containing a massive amount of IoT time-series data is taking up double the disk space expected. You cannot afford to double your storage arrays. What compaction strategy are you using, and what should you switch to?"

**Strong Answer**: "We are likely using **Size-Tiered Compaction Strategy (STCS)**, which is Cassandra's default. STCS requires ~50% free disk headroom at all times because to merge large files (e.g., three 100GB files), it must write a new 300GB file *before* it deletes the old ones. That's why it looks like it's taking double the space. 

Since it's IoT time-series data, we should switch to **Time-Window Compaction Strategy (TWCS)**. TWCS groups IoT data into discrete daily or hourly buckets and *never* merges across those time boundaries. Critically, when data hits its TTL (Time To Live), TWCS drops the entire file directly to the OS without any expensive compaction process, solving the space overhead completely."

---

### Q3: "Explain what happens if a database cluster suffers a 'Compaction Backlog' or 'Compaction Death Spiral'?"

**Strong Answer**: "A compaction backlog occurs when the rate of foreground writes (inserting data, flushing memtables to Level 0 SSTables) outpaces the background I/O threads' ability to sort and merge them. 
When this happens, the number of files in L0 explodes. Because L0 files have overlapping key boundaries, every single read query is now forced to scan 50 or 100 individual files instead of 1 or 2.

This spikes Read Amplification. P99 latency shoots up. Because reads take longer, CPU and I/O are saturated, which paradoxically starves the background compactions of resources even further, worsening the backlog. This is the 'death spiral.' The short-term fix is rate limiting foreground writes (backpressure) or raising the background compaction thread count/I/O limits to clear the L0 bottleneck."

---

### Q4: "How do you handle 'tombstones' efficiently in a system with massive deletes?"

**Strong Answer**: "In an LSM engine, a delete is an `INSERT` of a tombstone marker. If you have massive deletes, using STCS is dangerous because the tombstone and the original data might sit in separate tiered files and not encounter each other during a compaction pass for months, slowing down reads. 
For workloads with frequent deletes or updates, **Leveled Compaction Strategy (LCS)** is mandatory. LCS forces active, continuous merging of overlapping key ranges downward, ensuring that tombstones aggressively meet the original data and resolve, purging the dead data quickly and keeping read latencies stable."

---

## Whiteboard Exercise (5 minutes)

Draw the **RUM Conjecture** trade-off triangle and map the three Compaction Strategies to it.

```mermaid
flowchart TD
    %% RUM Triangle
    Read[Read Optmized<br>Low Read Amp] 
    Update[Write/Update Optimized<br>Low Write Amp]
    Memory[Space Optimized<br>Low Space Amp]
    
    Read --- Update
    Update --- Memory
    Memory --- Read

    %% Strategy Mapping
    LCS[**LCS** (Leveled)<br>Favors Read & Space<br>Fails at Write Amp] -.-> Read
    LCS -.-> Memory

    STCS[**STCS** (Size Tiered)<br>Favors Write Amp<br>Fails at Read & Space] -.-> Update
    
    TWCS[**TWCS** (Time Window)<br>Breaks the triangle<br>for Append-only Time-Series] -.-> Update
    TWCS -.-> Read
```

**Talking points while drawing**: "You can't have low read, write, and space amplification simultaneously. LCS trades write amplification (CPU/Disk burnout) for very predictable read latencies. STCS trades read latency (scanning many files) and space (requiring 50% free headroom) to favor writing fast. TWCS cheats the triangle, but only specifically for append-only data with a TTL."
