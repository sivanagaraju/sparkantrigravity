# The PACELC Theorem — Real-World Scenarios

> **Principal's Perspective:** When architects mismatch the business constraints of a domain to the PACELC profile of the datastore, the result is either unacceptably slow user experiences or catastrophic data anomalies resulting in financial loss or reputation damage.

---

## Scenario 1: The Multi-Region E-Commerce Shopping Cart

**The Business Problem:**
A global e-commerce giant needs to store user shopping carts. Users span the US, EU, and Asia.

**The Mistake (Choosing PC/EC):**
Architects chose a distributed SQL database (like CockroachDB) configured for strict internal consistency (`PC/EC`) across 3 continents, reasoning that "carts are critical transactional data."

**The Consequence:**
When a user in Tokyo clicks "Add to Cart", the request hits the local Tokyo node. But to commit, the database must replicate the write to a quorum, involving the US or EU nodes. `Latency = 150ms`. 
When the user clicks "View Cart", it must establish a read quorum to ensure no concurrent processes altered the cart. `Latency = 150ms`.
The sluggish UI leads to a 15% drop in conversion rate.

**The PACELC Realization:**
A shopping cart does *not* require strict consistency. If a user adds an item in Tokyo, and immediately logs into their phone via an EU VPN, it is acceptable if the EU session takes 2 seconds to see the updated cart.

**The Fix (Shifting to PA/EL):**
Migrate carts to an actively-replicated `PA/EL` datastore (like DynamoDB Global Tables or Cassandra). Writes are acknowledged locally (`<5ms`), providing instant UI feedback. The data syncs globally in the background. If a network partition occurs, users can still add items to their carts on both sides of the partition; the DB uses conflict resolution (like Last-Write-Wins or CRDTs) to merge the carts when the network heals.

```mermaid
graph TB
    classDef eu fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef us fill:#831843,stroke:#f43f5e,stroke-width:2px,color:#fff;
    classDef as fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#fff;
    
    subgraph EU_Region [Frankfurt (EU)]
        WebEU[API Server]:::eu
        DB_EU[(DB Replica)]:::eu
        WebEU -->|Sub-5ms| DB_EU
    end
    
    subgraph US_Region [Virginia (US)]
        WebUS[API Server]:::us
        DB_US[(DB Replica)]:::us
        WebUS -->|Sub-5ms| DB_US
    end
    
    subgraph AS_Region [Tokyo (Asia)]
        WebAS[API Server]:::as
        DB_AS[(DB Replica)]:::as
        WebAS -->|Sub-5ms| DB_AS
    end

    DB_EU -.->|Async Replication ~80ms| DB_US
    DB_US -.->|Async Replication ~150ms| DB_AS
    DB_AS -.->|Async Replication ~200ms| DB_EU
```

---

## Scenario 2: The Global Financial Ledger

**The Business Problem:**
A fintech company allows users to transfer balances instantly between international accounts. The ledger spans US and EU data centers.

**The Mistake (Choosing PA/EL):**
The architects chose Cassandra, configuring it with `Consistency = ONE` (`PA/EL`) because they were obsessed with a "sub-10ms API response time" KPI set by product managers.

**The Consequence:**
A user in London connects to the EU server, checks their balance (`$100`), and begins a transfer of `$100` to a friend. The EU server locally decrements the balance and responds "Success" instantly (`EL`).
Simultaneously, the user runs an automated script in the US connecting to the US server, checking their balance. The US server hasn't received the async update yet, sees the balance as `$100`, and transfers `$100` to a different account.
The background replication syncs, and the user's balance evaluates to `-$100`. The company loses money due to the classic "Double Spend" anomaly.

**The PACELC Realization:**
When dealing with invariants (e.g., `balance >= 0`), you **cannot** sacrifice Consistency for Latency. 

**The Fix (Shifting to PC/EC):**
Move the ledger to Spanner or CockroachDB. 
The business must accept that cross-region transfers will have a latency floor of `~80ms` to achieve quorum consensus. During a transatlantic fiber cut (`P`), the system will proudly halt processing (`PC`), preventing the double spend, rather than remaining available and allowing financial divergence.

---

## Scenario 3: The Social Media Feed architecture

**The Business Problem:**
A social network needs to process user posts and render their timelines. 

**The PACELC Architecture:**
This requires a blended approach.

**The "Write" Path (Posts):**
When a user posts a photo, they want immediate feedback. You use a `PA/EL` architecture.
The client writes to a local edge node and returns `HTTP 200 OK` instantly (`EL`). The user's app optimistically displays the photo. The write queues in Kafka and replicates globally.

**The "Read" Path (The Feed):**
When viewing the timeline, you also want speed (`EL`). You read from a local materialized view (Redis or Cassandra). It doesn't matter if you see a friend's post 3 seconds after they made it. The feed is eventually consistent.

**The "Account Settings" Path:**
If a user changes their password or updates visibility to "Private", this cannot be `EL`. If they change visibility to Private, and a friend loads the feed 50ms later, the friend should *not* see the restricted content.
This subsystem must be `PC/EC`. You force the write to achieve global synchronization, accepting the 200ms latency hit for a rare, security-critical operation. 

**The Lesson:**
Do not apply a single PACELC profile to your entire microservice or enterprise. Apply it per domain, per table, and precisely per query footprint.
