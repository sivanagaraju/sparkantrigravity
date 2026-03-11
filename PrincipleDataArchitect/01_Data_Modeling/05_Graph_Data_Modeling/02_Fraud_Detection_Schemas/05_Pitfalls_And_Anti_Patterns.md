# Fraud Detection Schemas — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Treating Graph Fraud Detection as a Standalone System

**The mistake**: Replacing rules and ML with graph analysis instead of using graph as a complementary layer.

**What breaks**: Graph analysis excels at structural pattern detection (rings, clusters) but is weak at individual transaction anomalies (unusual amount, strange time, geographic anomaly). Removing rules means you lose threshold alerts, velocity checks, and blacklist matching. Removing ML means you lose behavioral scoring.

**Detection**:

- Check if the fraud system has only a graph component (no rules engine, no ML model)
- Check if the graph score is used as the sole decision input (not combined with other signals)

**Fix**: Use graph as one layer in a multi-layer stack:

1. **Layer 1 — Rules**: Threshold, velocity, blacklist (catches obvious fraud)
2. **Layer 2 — Graph**: Pattern matching, proximity-to-fraud, community risk (catches coordinated fraud)
3. **Layer 3 — ML**: Combined features from rules + graph + behavioral data → risk score

The ML model's input should include graph-derived features (degree, centrality, community_risk, distance_to_fraud) alongside non-graph features (amount, time, location, velocity).

---

## Anti-Pattern 2: Running Community Detection Without Edge Filtering

**The mistake**: Running community detection (Louvain, Label Propagation) on the full graph including legitimate relationship types.

**What breaks**: Marketing campaigns, referral programs, and onboarding flows create dense legitimate clusters. Community detection algorithms interpret these as suspicious because of high connectivity. Result: 50,000 false positives from a referral campaign (see Real-World Scenarios post-mortem).

**Detection**:

- Check if community detection runs on all edge types or only suspicious ones
- Check false positive rate after batch pipeline runs vs after marketing campaigns

**Fix**: Filter edges before running community detection:

```cypher
// ❌ WRONG: Community detection on all edges
CALL gds.louvain.write({nodeQuery: 'MATCH (n:Account) RETURN id(n) AS id',
    relationshipQuery: 'MATCH (a:Account)-[r]->(b:Account) RETURN id(a) AS source, id(b) AS target'})

// ✅ CORRECT: Only include transaction and device-sharing edges
CALL gds.louvain.write({nodeQuery: 'MATCH (n:Account) RETURN id(n) AS id',
    relationshipQuery: 'MATCH (a:Account)-[r:TRANSACTED_WITH|OWNS_DEVICE]->(b:Account)
                         WHERE r.txn_time >= datetime() - duration("P90D")
                         RETURN id(a) AS source, id(b) AS target'})
```

---

## Anti-Pattern 3: No Query Timeout on Real-Time Traversals

**The mistake**: Allowing graph fraud queries to run indefinitely during transaction authorization.

**What breaks**: A single customer with 10M transaction edges (e.g., a large merchant) triggers a 2-hop traversal that expands to billions of nodes. The query takes 30 seconds, blocking the payment authorization. The payment gateway times out, and the customer sees a failed transaction.

**Detection**:

- Check P99 latency of real-time fraud queries. If P99 > 5× P50, there are tail-latency problems
- Check for correlation between fraud query latency and node degree

**Fix**: Implement multiple guards:

```python
# 1. Query-level timeout
session.run("MATCH ... RETURN ...", timeout=50)  # 50ms max

# 2. Degree-aware query routing
def score_transaction(account_id):
    degree = get_account_degree(account_id)
    if degree > 100_000:
        # Super node: use pre-computed features from cache
        return get_cached_risk_score(account_id)
    else:
        # Normal node: real-time graph traversal
        return run_graph_traversal(account_id)

# 3. Circuit breaker: if graph DB is slow, fall back to rules-only
if graph_latency_p95 > 100:  # ms
    return rules_only_score(transaction)
```

---

## Anti-Pattern 4: Static Graph (No Real-Time Edge Updates)

**The mistake**: Loading the fraud graph via nightly batch only. Fraud patterns that emerge during the day are invisible until the next batch.

**What breaks**: A fraudster creates 5 accounts at 9 AM, links them to the same device, and starts laundering money at 10 AM. The batch graph (loaded at 2 AM) doesn't include these new nodes/edges. The real-time fraud query traverses the stale graph and finds no suspicious patterns.

**Detection**:

- Check graph freshness: when was the last edge created? If it's >1 hour old, the graph is stale
- Correlate fraud detection miss rate with time-of-day (higher misses during the day = stale graph)

**Fix**: Stream graph mutations in real-time:

```
Kafka topic: fraud.graph.mutations
  → Consumer: Graph Mutation Service
  → Neo4j: CREATE/MERGE nodes and edges
  
Messages:
  {type: "NODE_CREATE", label: "Account", properties: {...}}
  {type: "EDGE_CREATE", type: "TRANSACTED_WITH", src: ..., dst: ..., properties: {...}}
  {type: "EDGE_CREATE", type: "OWNS_DEVICE", src: ..., dst: ...}
```

---

## Anti-Pattern 5: No Feedback Loop (Never Learning from False Positives)

**The mistake**: Generating fraud alerts from graph patterns but never feeding investigation outcomes (true positive / false positive) back into the model.

**What breaks**: The same false positive patterns keep triggering alerts. Investigators waste time on the same types of non-fraud clusters. The system's precision never improves.

**Fix**: Close the feedback loop:

1. Investigators mark each alert as TRUE_POSITIVE or FALSE_POSITIVE
2. Weekly retraining: ML model uses investigation outcomes as labels
3. Graph algorithms incorporate feedback: nodes marked as false positive reduce the community risk score of their cluster
4. Track precision/recall over time — if precision drops below 50%, the system is generating more noise than signal

---

## Decision Matrix — When Graph Fraud Detection Is the WRONG Choice

| Scenario | Why Graph Is Wrong | Better Alternative |
|---|---|---|
| Simple threshold monitoring (amount > $10K) | No relationships needed — pure transaction attribute | Rules engine |
| Credit scoring (individual risk assessment) | Individual attributes, not network structure | Traditional ML (logistic regression, GBM) |
| Low-volume transactions (<1K/day) | Graph infrastructure overhead not justified | Manual review + simple rules |
| Compliance reporting (SAR filing) | Graph supports investigation but filing is a document workflow | Case management system |
| Real-time with <10ms budget | Graph traversal adds 15-50ms latency | Pre-computed feature lookup |
