# Embedding vs Referencing — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Unbounded Embedded Arrays

**The mistake**: Embedding a child collection that grows without limit. User activities, product reviews, chat messages — any array that accumulates over time.

```javascript
// ❌ WRONG: Embedding all order history in user document
{
  _id: "user-123",
  name: "Alice",
  orders: [
    { order_id: "O-1", date: "2023-01-01", total: 99.99 },
    // ... after 3 years: 2,000 orders, document = 2MB
    // Power customer after 10 years: 10,000 orders, document = 10MB
    // Eventually: exceeds 16MB MongoDB limit
  ]
}
```

**Detection**:

- Monitor document sizes: `db.collection.aggregate([{$project: {size: {$bsonSize: "$$ROOT"}}}, {$sort: {size: -1}}, {$limit: 10}])`
- Alert when max document size exceeds 5MB (warning) or 10MB (critical)

**Fix**: Move unbounded data to a separate collection. Optionally embed a bounded subset:

```javascript
// ✅ CORRECT: Separate collection + embedded summary
// User document (fixed size)
{ _id: "user-123", name: "Alice", order_count: 2000,
  recent_orders: [/* last 5 only */] }

// Orders collection (unbounded, paginated)
{ order_id: "O-2000", user_id: "user-123", date: "2024-03-15", ... }
```

---

## Anti-Pattern 2: Referencing Everything (NoSQL Used as Relational)

**The mistake**: Putting every entity in a separate collection with foreign keys — treating MongoDB like PostgreSQL.

```javascript
// ❌ WRONG: Product, price, and category in 3 collections
// Product display requires 3 queries (no server-side JOINs in most NoSQL)
const product = db.products.findOne({ _id: productId });
const price = db.prices.findOne({ product_id: productId, current: true });
const category = db.categories.findOne({ _id: product.category_id });
// 3 round trips. 15ms total. Could be 3ms with embedding.
```

**Fix**: Embed data that's always read together:

```javascript
// ✅ CORRECT: Embed price and category name
{
  _id: productId,
  name: "MacBook Pro",
  price: { amount: 2499, currency: "USD" },
  category: { id: "electronics", name: "Electronics" },
  // All display data in one document. 1 read. 3ms.
}
```

---

## Anti-Pattern 3: Not Maintaining Embedded Data Consistency

**The mistake**: Embedding customer data in orders but never updating it when the customer changes their name or email.

**What breaks**: Customer changes name from "Alice Smith" to "Alice Johnson." All 500 past orders still show "Alice Smith." Customer support can't find orders by current name.

**Detection**: Compare embedded data against source:

```javascript
// Find orders where embedded customer name doesn't match source
db.orders.aggregate([
  { $lookup: {
      from: "customers",
      localField: "customer.customer_id",
      foreignField: "_id",
      as: "current_customer"
  }},
  { $unwind: "$current_customer" },
  { $match: {
      $expr: { $ne: ["$customer.name", "$current_customer.name"] }
  }},
  { $count: "stale_orders" }
]);
```

**Fix**: Choose one of three strategies:

1. **Accept staleness**: Don't update embedded data. Orders show the name at the time of order (often correct for shipping receipts).
2. **Change stream sync**: Use MongoDB Change Streams to fan out updates asynchronously (eventual consistency, <5s lag).
3. **Write-time update**: Update all embedded copies in a transaction (strong consistency, higher write cost).

---

## Anti-Pattern 4: Using $lookup in Hot Read Paths

**The mistake**: Using MongoDB's `$lookup` (aggregation JOIN) in latency-sensitive API endpoints.

**What breaks**: `$lookup` is a server-side left outer join. It's significantly slower than a simple `findOne` because it crosses collections. In hot paths (>1000 req/s), `$lookup` creates server CPU pressure and unpredictable latency.

**Detection**: Check slow query log for aggregation pipelines containing `$lookup`. Monitor P95 latency for endpoints using `$lookup`.

**Fix**: Pre-embed the data you need (extended reference or subset pattern). Reserve `$lookup` for:

- Batch analytics jobs
- Admin/internal tools
- Low-traffic endpoints (<100 req/s)

---

## Anti-Pattern 5: Ignoring Document Size Limits by Database

**The mistake**: Assuming all document databases have the same size limits.

| Database | Max Document Size | Common Violation |
|---|---|---|
| MongoDB | 16 MB | Embedding media, logs, or activity arrays |
| DynamoDB | 400 KB | Embedding even moderate arrays (50 items at 5KB each = 250KB) |
| Firestore | 1 MB | Embedding nested maps with user-generated content |
| Couchbase | 20 MB | Less common, but embedding binary data |

**Fix**: Design with the tightest limit in mind. For DynamoDB's 400KB limit, even "small" embedded arrays can exceed the limit. Use the multi-item-per-partition approach (items in same partition key as separate sort key entries).

---

## Decision Matrix — Common Anti-Pattern Mapping

| Relationship | Anti-Pattern | Correct Pattern |
|---|---|---|
| User → addresses (1:few) | Reference (over-normalized) | Embed (bounded, always together) |
| Post → comments (1:thousands) | Embed all (unbounded) | Reference + subset (top 5 embedded) |
| Order → customer (many:1) | Full embed (denormalization tax) | Extended reference (name+email only) |
| Product → reviews (1:millions) | $lookup in hot path | Computed stats embedded + reference for list |
| User → settings (1:1) | Separate collection | Embed (always read together) |
