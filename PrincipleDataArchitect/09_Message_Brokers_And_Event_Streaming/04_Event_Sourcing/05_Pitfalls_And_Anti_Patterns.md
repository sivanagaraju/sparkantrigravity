# Event Sourcing Architecture — Pitfalls and Anti-Patterns

## Anti-Pattern 1: The "Event Schema Evolution" Nightmare

### The Trap
In 2020, you launch your Event Sourcing architecture. You create a `UserCreated` event that explicitly requires a strictly formatted `first_name` and `last_name`.
In 2024, the business decides to just collect a single `full_name`. Your new code expects a `full_name` key in the JSON payload.
When your 2024 code attempts to replay the event log from 2020 to rebuild the state, it crashes instantly because it cannot find the `full_name` key on the old historical events.

### Concrete Fix
You can **never, ever alter historical events**. The Event Store must be strictly immutable. 
You must handle schema evolution purely in the consuming read-layer. The `apply(event)` code must natively support processing "V1" events and gracefully transforming them in memory during Rehydration, while the new code accepts "V2" events natively.

---

## Anti-Pattern 2: Infinite Replay Boot Times

### The Trap
An e-commerce shopping cart has been active for 5 years. It contains 250,000 distinct `ItemAdded`, `ItemRemoved`, and `DiscountApplied` events.
Every single time exactly the user logs in and loads the UI, your server queries all 250,000 rows and individually runs them sequentially through memory to calculate the final price of the cart. The API takes 48 seconds to respond.

### Concrete Fix
**Snapshots.** You must strictly run a background cron job that periodically securely rebuilds the aggregate and saves it to a standard CRUD caching table. Upon boot, the application simply grabs the absolute latest Snapshot state, and then only replays the minimal delta of new events that naturally occurred exactly *after* the snapshot timestamp.
