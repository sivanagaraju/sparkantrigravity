# Spanner, CockroachDB, TiDB — Interview Angle

> **Principal's Perspective:** In a FAANG Staff/Principal systems design interview, simply dropping the word "Spanner" is a massive red flag if you don't know the consequences of that choice. Interviewers use NewSQL to explicitly test whether you understand the speed of light limits and complex failure domain planning.

---

## The "What DB to Choose" Flowchart

When given a global system design problem (e.g., "Design Ticketmaster", "Design a Global Payment Gateway"):

**1. "Can we use asynchronous sharded MySQL or Cassandra?"**
* Does the business accept eventual consistency? (e.g., Social media likes, logs) => **No**, use Cassandra.
* Can transactions be isolated absolutely to a single geographic shard? (e.g., a German user *never* shares a transactional boundary with a US user) => **No**, use manually sharded MySQL.

**2. "When is Cockroach/Spanner the right answer?"**
* When money or critical inventory is moving across global boundaries where cross-shard conflicts are guaranteed, and manual 2PC application logic is too brittle to maintain.
* **Keywords to throw:** "Linearizability," "Strict Serializable," "Multi-Region Survivability," "Data Domiciles for GDPR."

---

## Sample Interview Questions & Deep Answers

### Q1: "You chose a globally distributed SQL database like Spanner. Walk me through the exact latency cost of an `INSERT` originating from an App Server in London, if the primary users are in the US but we replicate globally."

**Weak Answer:** "Spanner handles global replication automatically, so the insert is safe."

**Principal Answer:** "The latency cost will be heavily dependent on physics. Because Spanner uses TrueTime and Paxos, to achieve an `INSERT`, we must hit a Paxos quorum (usually an overarching majority across 5 regions to survive whole-region failures). 
If the Paxos Leader for that row's range is in `us-east`, the London App Server forwards the request to `us-east` (Round trip 1). Then `us-east` asks `us-west`, `eu-west`, and `asia` for consensus. It waits for the fastest quorum. It also mandates a TrueTime commit wait (approx 7ms). 
So, `London -> US-East (40ms) + Consensus (40ms) + TrueTime (7ms) = ~80-90ms latency floor`.
I would explicitly flag to the product team that a simple database insert will take ~100ms, heavily influencing caching and synchronous API response strategies."

### Q2: "How does CockroachDB maintain correctness without atomic clocks?"

**Weak Answer:** "It uses normal NTP and hopes for the best."

**Principal Answer:** "CockroachDB uses Hybrid Logical Clocks (HLC), which fuse the host's actual NTP wall time with a logical tick counter. Every time nodes talk to each other via RPCs, they gossip the highest known timestamp, dragging slower clocks forward artificially.
Because clock drift is inevitable, Cockroach mandates a strict 'Maximum Offset' threshold (default 500ms). If a transaction attempts to commit and reads a conflicting value falling *within* that 500ms uncertainty window across nodes, the database triggers a 'Transaction Restart'. This sacrifices some throughput (retries) to guarantee consistency without bespoke Google hardware. If a system's NTP daemon drifts past 500ms permanently, the node self-terminates to preserve data integrity."

### Q3: "If you have a table storing billions of log lines, how do TiDB or Cockroach scale the primary key?"

**Weak Answer:** "Just add more nodes; the distributed architecture automatically shards it."

**Principal Answer:** "That's a trap. If I use a standard sequential `AUTO_INCREMENT` or timestamp as the primary key on a fast-growing table, all new inserts are appending to the exact same physical Sorted Key-Value range. 
This routes 100% of my cluster's write traffic to a single node holding the Raft Leader for that specific final segment. The other 99 nodes sit idle. 
To achieve linear scaling, I must hash the primary key or use a completely randomized UUID to spray queries evenly across all pre-split Raft ranges. Alternatively, I can use TiDB's `SHARD_ROW_ID_BITS` to artificially prefix the integers beneath the SQL layer."

---

## Whiteboarding the 2PC in Distributed SQL

Draw this quickly to show the intersection of SQL execution and KV consensus:

Draw this quickly to show the intersection of SQL execution and KV consensus:

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as Gateway Node
    participant TR as Transaction Record
    participant A as Row A (Raft X)
    participant B as Row B (Raft Y)

    C->>GW: 1) BEGIN; UPDATE A=A-1, B=B+1; COMMIT;
    GW->>TR: 2) Create Record (PENDING)
    
    par Send Intents
        GW->>A: 3) Write Intent: A-1 -> Ptrs to TR
        GW->>B: 3) Write Intent: B+1 -> Ptrs to TR
    end
    
    Note over A,B: Wait for Raft Quorum ACKs
    
    GW->>TR: 4) Update Record (COMMITTED)
    GW-->>C: 5) Return Client Success (ACK)
    
    Note over GW,B: Async: Wipe intents to committed values
```

**Talking Points:** "The client is successfully acknowledged *before* the intents on A and B are physically wiped clean. If a reader hits A or B while they still look like Intents, the reader checks Group Z to see if the transaction was committed or aborted." 
