# Event Storming — FAANG War Stories & Real-World Scenarios

> How Netflix, Amazon, LinkedIn, Uber, and Microsoft use this. Scale numbers, production incidents, lessons learned.

---

## Netflix: Content Lifecycle Domain Discovery

### The Problem

Netflix manages content across 190 countries, each with different licensing rights, languages, and regulatory requirements. When they needed to redesign their content metadata pipeline, no single person understood the entire content lifecycle.

### How Event Storming Helped

Netflix ran a Big Picture Event Storming session with content licensing, encoding, localization, and product teams. The event timeline revealed:

```
Content Licensed → Master Asset Received → Encoding Started → Encoding Completed →
QC Initiated → QC Passed/Failed → Metadata Enriched → Localization Started →
Subtitle Created → Dub Created → Localization Completed →
Rights Window Opened (per country) → Content Published → Content Surfaced (personalization) →
Content Watched → Engagement Scored → Rights Window Closed → Content Removed
```

### Key Discovery

The team discovered that "Content Published" meant **completely different things** to three teams:

- **Encoding team**: "The video file is on CDN"
- **Metadata team**: "The title, description, and artwork are in the catalog"
- **Rights team**: "The licensing window is open for this country"

This hot spot led to splitting "Content Published" into three separate domain events, each owned by a different bounded context. This directly shaped the Kafka topic design in their **Keystone** event pipeline.

### Scale

- 17,000+ titles
- 200M+ subscribers
- Events processed: ~100 billion/day across all content interaction events

---

## Amazon: The Order Aggregate That Wasn't One

### The Problem

Amazon's retail data warehouse had a single `orders` table with 300+ columns. Query performance was degrading, and different teams kept adding columns for their own needs.

### How Event Storming Revealed the Fix

During an Event Storming session, the team discovered that "Order" was actually **five distinct bounded contexts** with completely different lifecycles:

| Bounded Context | Key Events | Why It's Separate |
|---|---|---|
| **Cart** | Cart Updated, Item Added, Coupon Applied | Ephemeral, high-write, low-read |
| **Checkout** | Payment Initiated, Address Validated, Payment Captured | Transactional, strong consistency required |
| **Fulfillment** | Inventory Reserved, Shipment Created, Dispatched, Delivered | Long-running, event-driven |
| **Returns** | Return Requested, Inspection Passed, Refund Issued | Reverse flow, separate SLA |
| **Customer Service** | Complaint Filed, Escalation Triggered, Resolution Reached | Unstructured, NLP-heavy |

### The Result

The monolithic 300-column `orders` table was replaced with 5 domain-specific fact tables and a conformed `dim_order` dimension. Query performance improved 10-50x because each query only scanned the relevant subset of columns.

---

## LinkedIn: Activity Feed Domain Discovery

### The Problem

LinkedIn's activity feed ("John liked a post", "Jane started a new position") needed to serve 900M+ members with sub-200ms latency. The data model was becoming a bottleneck.

### Event Storming Discovery

The team identified 47 distinct activity event types across 12 bounded contexts:

```
Networking:     Connection Requested → Connection Accepted → Connection Removed
Content:        Post Created → Post Liked → Post Commented → Post Shared → Post Reported  
Career:         Position Updated → Company Changed → Skill Added → Endorsement Received
Jobs:           Job Posted → Job Applied → Application Reviewed → Interview Scheduled
Messaging:      Message Sent → Message Read → Group Created
Learning:       Course Started → Course Completed → Certificate Earned
```

### Architectural Impact

Each bounded context became a **separate Kafka topic namespace** with its own schema registry. The activity feed service consumed events from all 12 namespaces and materialized them into a per-user timeline using a custom read model (CQRS pattern).

---

## Uber: Ride Matching as Event Flow

### The Discovery

Uber's ride-matching domain was initially modeled as a simple `rides` table. Event Storming revealed it was actually a complex state machine:

```
Rider Requested Ride → Driver Matched → Driver En Route → Driver Arrived →
Rider Picked Up → Ride In Progress → Route Deviated → 
Ride Completed → Fare Calculated → Surge Pricing Applied → Payment Processed →
Rider Rated Driver → Driver Rated Rider → Ride Archived
```

**Hot spot**: "What happens when the driver cancels after accepting?" — This edge case had no data model support, causing silent data loss in the DW.

### Scale

- 28M rides/day
- Events per ride: 15-25 (including real-time GPS pings)
- Total event volume: ~500M events/day just for the ride-matching domain

---

## Key Lessons from FAANG Event Storming

| Lesson | Why It Matters |
|---|---|
| **An "entity" is usually multiple bounded contexts** | The order, ride, or content that seems like one thing is usually 3-5 separate domain concepts |
| **Hot spots are gold** | They reveal edge cases that will become bugs in your data model |
| **Events ≠ CRUD operations** | "Customer Updated" is useless. "Customer Upgraded Plan" is actionable |
| **Involve the quietest people** | The customer service rep who handles escalations knows failure modes no engineer has seen |
| **Photograph the wall** | The physical output of Event Storming IS your first-draft data model |
