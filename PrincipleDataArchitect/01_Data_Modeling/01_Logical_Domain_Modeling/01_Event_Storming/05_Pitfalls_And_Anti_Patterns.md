# Event Storming — Common Pitfalls & Anti-Patterns

> The top mistakes people make, why they are dangerous, and how to detect and fix them.

---

## ❌ Pitfall 1: Skipping Event Storming Entirely

### What Happens

The architect designs the data model from technical assumptions: "We need a `users` table, an `orders` table, a `products` table."

### Why It's Dangerous

You model the structure you *assume* exists, not the one the business actually needs. Six months later: "But we also needed to track abandoned carts, and the schema doesn't support it. We need a migration."

### The Fix

Event Storming takes 2-4 hours. A schema migration at scale takes 2-4 months. The ROI is infinite.

---

## ❌ Pitfall 2: Only Engineers in the Room

### What Happens

Five backend engineers map out the "Order" process based on their understanding of the code.

### Why It's Dangerous

Engineers know what the **code** does. They don't know what the **business** does. Hidden processes like "manual fraud review by the Trust & Safety team" or "exception handling by customer support" are invisible in the code but critical in the data model.

### The Fix

Minimum viable participant list:

- 1-2 Engineers (they know the technical constraints)
- 1 Product Manager (they know the user journeys)
- 1 Domain Expert (customer service, operations, finance — they know reality)
- 1 QA/Analyst (they know the edge cases)

---

## ❌ Pitfall 3: Writing Events as CRUD Operations

### What Happens

```
❌ WRONG:
Customer Created → Customer Updated → Customer Updated → Customer Deleted

✅ RIGHT:
Customer Registered → Customer Verified Email → Customer Upgraded Plan → 
Customer Changed Address → Customer Subscribed Newsletter → Customer Churned
```

### Why It's Dangerous

CRUD events carry no **business meaning**. "Customer Updated" tells you nothing about *what* changed or *why*. Your downstream analytics, feature store, and ML models need business semantics, not database operations.

### The Fix

Use the "newspaper test": Would a business journalist write "Customer Updated"? No. They'd write "Customer Upgraded to Premium Plan." That's your event name.

---

## ❌ Pitfall 4: Not Capturing Hot Spots

### What Happens

The facilitator smooths over disagreements: "Let's not get stuck on this, we'll figure it out later."

### Why It's Dangerous

Hot spots are the **most valuable output** of Event Storming. A disagreement about "When is an order 'confirmed'?" means your data model will have an ambiguous `order_status` column that different teams interpret differently — leading to conflicting reports, wrong dashboards, and broken ML models.

### The Fix

Mark every disagreement with a red dot (⚡ Hot Spot). After the session, each hot spot becomes an Architecture Decision Record (ADR) that must be resolved before schema design begins.

### Example Hot Spots That Became ADRs

| Hot Spot | ADR Decision |
|---|---|
| "Is an order 'confirmed' before or after payment?" | ADR-042: Order is confirmed AFTER payment captured, not after checkout |
| "Does 'revenue' include returns?" | ADR-043: Gross revenue includes returns; Net revenue excludes them. Both are tracked |
| "Who owns the 'product catalog' data?" | ADR-044: Product team owns catalog; Marketing team owns display metadata |

---

## ❌ Pitfall 5: One Giant Bounded Context

### What Happens

Everything lives in the "Order" context: cart events, payment events, shipping events, return events, review events — all in one giant cluster.

### Why It's Dangerous

If everything is one bounded context, you'll end up with one monolithic database, one gigantic Kafka topic, and one team responsible for everything. This is the monolith anti-pattern applied to data architecture.

### How to Detect

- If a single aggregate has > 15 events, it's probably multiple aggregates
- If two events in the same context have **different owners** (e.g., the Payment team owns "Payment Captured" but the Fulfillment team owns "Shipment Dispatched"), they belong in different contexts

### The Fix

Apply the "pivot event" test: Find events where the **responsible team changes**. That's a bounded context boundary.

```
Cart Updated (Product team) → Payment Captured (Payments team) ← BOUNDARY
Payment Captured (Payments team) → Shipment Created (Logistics team) ← BOUNDARY
```

---

## ❌ Pitfall 6: Doing Event Storming Once and Never Again

### What Happens

The team runs one Event Storming session during the initial project kickoff, then never revisits it.

### Why It's Dangerous

Business processes evolve. New products launch. Regulations change. The data model that was correct in January is wrong by June.

### The Fix

- Run a **Big Picture refresh** quarterly (1-2 hours)
- Run a **Process Modeling session** whenever a major feature is being designed
- Keep the event timeline as a living document (Miro board, not a photograph that sits in Confluence forever)

---

## Detection Checklist: Are You Making These Mistakes?

| Symptom | Likely Pitfall |
|---|---|
| Data model was designed by 1-2 engineers without business input | Pitfall 2 |
| Event schemas have names like `entity_updated` | Pitfall 3 |
| Teams disagree on column definitions | Pitfall 4 (unresolved hot spots) |
| One Kafka topic has 50+ event types | Pitfall 5 (one giant context) |
| Data model hasn't been reviewed against business processes in 6+ months | Pitfall 6 |
