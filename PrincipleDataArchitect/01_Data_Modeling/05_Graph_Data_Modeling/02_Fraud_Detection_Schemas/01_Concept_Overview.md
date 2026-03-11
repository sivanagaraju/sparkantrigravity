# Fraud Detection Schemas — Concept Overview

> Why graphs are the superior tool for detecting fraud patterns that relational databases miss.

---

## Why This Exists

**Origin**: Fraud detection moved from rule-based systems to graph analysis in the 2010s when financial institutions realized that fraudsters operate in **networks** — rings of connected accounts, shared devices, reused identities. Relational queries can check individual rules ("transaction > $10K"), but cannot efficiently detect structural patterns ("three accounts share a phone number, a device fingerprint, and a shipping address, but have different names").

**The problem it solves**: First-party fraud (application fraud using synthetic identities) evades traditional rule-based systems because each individual application looks legitimate. Only when you see the **network** — shared attributes connecting seemingly unrelated applications — do fraud rings become visible.

## Mindmap

```mermaid
mindmap
  root((Fraud Detection Graphs))
    Fraud Types
      First-party fraud
        Synthetic identity
        Application fraud
        Bust-out schemes
      Third-party fraud
        Account takeover
        Card-not-present
        Identity theft
      Collusion
        Insider threats
        Fraud rings
        Money laundering
    Graph Patterns
      Shared attributes
        Same phone across accounts
        Same device fingerprint
        Same address different names
      Ring detection
        Circular money transfers
        Connected shell companies
        Layered ownership
      Velocity patterns
        Rapid new-account creation
        Burst of transactions
    Graph Algorithms
      Community detection - Louvain
      PageRank - influence scoring
      Shortest path - money flow
      Triangle counting - collusion
    Why Not Relational?
      Unknown depth of connections
      Many-to-many relationships
      Pattern matching across types
      Real-time sub-second requirement
```

## Key Terminology

| Term | Definition |
|---|---|
| **Fraud Ring** | A group of connected entities (accounts, people, devices) exhibiting coordinated fraudulent behavior |
| **Shared Attribute** | A property (phone, email, device, IP, address) connecting seemingly unrelated accounts |
| **Synthetic Identity** | A fabricated identity combining real and fake information to open accounts |
| **Community Detection** | Graph algorithm that identifies densely connected subgraphs (potential fraud rings) |
| **Link Analysis** | Examining relationships between entities to uncover hidden connections |
