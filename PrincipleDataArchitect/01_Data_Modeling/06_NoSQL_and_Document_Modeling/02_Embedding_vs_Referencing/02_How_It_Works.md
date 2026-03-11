# Embedding vs Referencing — How It Works (Deep Internals)

> HLD, storage impact, query patterns, hybrid strategies, and data flow.

---

## High-Level Design — Embedding vs Referencing

```mermaid
flowchart LR
    subgraph "Embedding (Denormalized)"
        DOC_E["Order Document"]
        EMBED["{ order_id: 'O-1',<br/>  customer: {name, email},<br/>  items: [<br/>    {product, qty, price},<br/>    {product, qty, price}<br/>  ]<br/>}"]
        READ_E["1 read → complete order"]
    end
    
    subgraph "Referencing (Normalized)"
        DOC_R1["Order Document<br/>{ order_id: 'O-1',<br/>  customer_id: 'C-1',<br/>  item_ids: ['I-1', 'I-2']<br/>}"]
        DOC_R2["Customer Document<br/>{ _id: 'C-1',<br/>  name, email<br/>}"]
        DOC_R3["Item Documents<br/>{ _id: 'I-1', ... }<br/>{ _id: 'I-2', ... }"]
        READ_R["3 reads → complete order"]
    end
    
    DOC_E --- EMBED --- READ_E
    DOC_R1 --- READ_R
    DOC_R2 --- READ_R
    DOC_R3 --- READ_R
    
    style READ_E fill:#4ECDC4,color:#fff
    style READ_R fill:#FF6B35,color:#fff
```

---

## ER Diagram — Document Schema Patterns

```mermaid
erDiagram
    ORDER_EMBEDDED {
        objectid _id PK
        string order_id
        object customer "EMBEDDED: name, email, address"
        array items "EMBEDDED: product, qty, price"
        decimal total
        string status
        timestamp created_at
    }
    
    ORDER_REFERENCED {
        objectid _id PK
        string order_id
        objectid customer_id FK "REFERENCE to customers"
        decimal total
        string status
        timestamp created_at
    }
    
    CUSTOMER {
        objectid _id PK
        string name
        string email
        object address
    }
    
    ORDER_ITEM {
        objectid _id PK
        objectid order_id FK
        string product_name
        int quantity
        decimal unit_price
    }
    
    ORDER_REFERENCED }|--|| CUSTOMER : "references"
    ORDER_REFERENCED ||--o{ ORDER_ITEM : "has items"
```

---

## Decision Flowchart — Embed or Reference?

```mermaid
flowchart TD
    START([New relationship to model])
    
    START --> CARD{Cardinality?}
    
    CARD -->|"1:1"| EMBED_YES["✅ EMBED"]
    CARD -->|"1:few (<50)"| BOUNDED{Bounded?}
    CARD -->|"1:many (50-10K)"| ACCESS{Read together?}
    CARD -->|"1:millions"| REF_YES["✅ REFERENCE"]
    CARD -->|"many:many"| REF_YES
    
    BOUNDED -->|Yes| EMBED_YES
    BOUNDED -->|"No (grows)"| REF_YES
    
    ACCESS -->|"Always together"| SIZE{Total doc < 16MB?}
    ACCESS -->|"Often separately"| REF_YES
    
    SIZE -->|Yes| EMBED_YES
    SIZE -->|"Risk of exceeding"| HYBRID["⚠️ HYBRID<br/>(subset pattern)"]
    
    style EMBED_YES fill:#4ECDC4,color:#fff
    style REF_YES fill:#FF6B35,color:#fff
    style HYBRID fill:#F39C12,color:#fff
```

---

## Storage Internals — Document Size Impact

```javascript
// ============================================================
// Size comparison: embedded vs referenced
// ============================================================

// EMBEDDED: All order data in one document
// An order with 50 items, each item ~200 bytes
// Document size: ~200 + 50 * 200 = ~10.2 KB ✅ OK
// An order with 10,000 items (wholesale bulk order):
// Document size: ~200 + 10,000 * 200 = ~2 MB ⚠️ Getting large
// An order with 100,000 items:  
// Document size: ~200 + 100,000 * 200 = ~20 MB ❌ EXCEEDS 16MB LIMIT

// REFERENCED: Order header + separate item documents
// Order document: ~500 bytes (always fixed)
// Item documents: 200 bytes each (separate collection)
// Never exceeds limits. But: N+1 reads required.
```

---

## Hybrid Patterns — Detailed

### Pattern 1: Subset Pattern

```javascript
// Full product document (product collection)
{
  _id: ObjectId("..."),
  name: "MacBook Pro 16-inch",
  price: 2499.00,
  description: "Full 2000-word product description...",
  specs: { cpu: "M3 Max", ram: "36GB", storage: "1TB", ... },
  reviews: [ /* hundreds of reviews */ ],
  images: [ /* 20 high-res image URLs */ ],
  inventory: { warehouse_a: 50, warehouse_b: 120, ... }
}
// Size: ~50KB with reviews

// Order with SUBSET pattern — embed only what's needed
{
  _id: ObjectId("..."),
  order_id: "O-456",
  items: [
    {
      product_id: ObjectId("..."),  // reference for full details
      name: "MacBook Pro 16-inch",  // embedded subset
      price: 2499.00,              // embedded (snapshot at order time)
      image: "https://..."          // embedded (thumbnail only)
    }
  ]
}
// Size: ~500 bytes per item. No need to $lookup for order display.
```

### Pattern 2: Extended Reference

```javascript
// Instead of just storing customer_id, store key fields too
{
  _id: ObjectId("..."),
  order_id: "O-456",
  customer: {
    _id: ObjectId("..."),    // reference ID
    name: "Alice Johnson",    // embedded for display
    email: "alice@example.com" // embedded for notifications
    // Full address, preferences, etc. NOT embedded — reference if needed
  },
  items: [ /* ... */ ]
}
// Avoids $lookup for 90% of use cases (display order)
// $lookup only needed for full customer profile
```

### Pattern 3: Computed Pattern

```javascript
// Product with embedded review statistics (pre-computed)
{
  _id: ObjectId("..."),
  name: "MacBook Pro 16-inch",
  price: 2499.00,
  // Pre-computed from reviews collection
  review_stats: {
    count: 1247,
    average: 4.7,
    distribution: { "5": 890, "4": 250, "3": 70, "2": 20, "1": 17 }
  }
  // Individual reviews stored in separate collection
}
// Product listing page needs count+average — no aggregation query needed
// Review detail page $lookups individual reviews
```

---

## Sequence Diagram — $lookup (Application-Level JOIN)

```mermaid
sequenceDiagram
    participant App as Application
    participant Mongo as MongoDB
    
    Note over App,Mongo: REFERENCING: Multiple round trips
    
    App->>Mongo: db.orders.findOne({order_id: "O-456"})
    Mongo->>App: { order_id: "O-456",<br/>customer_id: "C-1",<br/>item_ids: ["I-1", "I-2"] }
    
    App->>Mongo: db.customers.findOne({_id: "C-1"})
    Mongo->>App: { name: "Alice", email: "..." }
    
    App->>Mongo: db.items.find({_id: {$in: ["I-1", "I-2"]}})
    Mongo->>App: [{ product: "..." }, { product: "..." }]
    
    Note over App: 3 round trips. Total: ~15ms
    
    Note over App,Mongo: EMBEDDING: Single read
    
    App->>Mongo: db.orders.findOne({order_id: "O-456"})
    Mongo->>App: { order_id: "O-456",<br/>customer: { name, email },<br/>items: [{ product, qty }, ...] }
    
    Note over App: 1 round trip. Total: ~3ms
```

---

## Data Flow — Maintaining Embedded Data Consistency

```mermaid
flowchart LR
    subgraph "Write Path (Denormalization Tax)"
        UPDATE["Customer name changes<br/>from 'Alice' to 'Alice J.'"]
        SOURCE["Update customers collection"]
        FAN["Fan-out updates to:<br/>• All orders with embedded customer<br/>• All reviews with embedded author<br/>• All comments with embedded user"]
    end
    
    subgraph "Strategies"
        SYNC["Synchronous<br/>(transaction, slow)"]
        ASYNC["Asynchronous<br/>(Change Stream, eventual)"]
        STALE["Accept staleness<br/>(snapshot at write time)"]
    end
    
    UPDATE --> SOURCE --> FAN
    FAN --> SYNC
    FAN --> ASYNC
    FAN --> STALE
    
    style FAN fill:#E74C3C,color:#fff
```

The **denormalization tax**: When you embed customer data in orders, every customer name change requires updating all orders containing that customer. This is the cost of embedding.

---

## Comparison — Embedding vs Referencing Across Databases

| Aspect | MongoDB | DynamoDB | Firestore | Couchbase |
|---|---|---|---|---|
| Max document size | 16 MB | 400 KB | 1 MB | 20 MB |
| Server-side JOIN | `$lookup` (aggregation) | None | None | N1QL `JOIN` |
| Embedding support | Nested documents + arrays | Nested maps + lists | Nested maps + arrays | Nested JSON |
| Transaction support | Multi-document ACID | TransactWriteItems (25 items) | Batch writes | Multi-doc ACID |
| Change streams | Yes (for fan-out) | DynamoDB Streams | Snapshot listeners | DCP |
