# 🧠 Mind Map – Embedding vs Referencing

---

## How to Use This Mind Map

- **For Revision:** Scan the hierarchical headers and bullets to recall the Speed vs Scale trade-off — from 1:1 embed rules through hybrid patterns — in 60 seconds.
- **For Application:** Before designing a new document schema, jump to **Techniques & Patterns** for the cardinality decision matrix.
- **For Interviews:** Use the **Interview Angle** branch to rehearse the "10,000 comments on a post" question and the Subset Pattern answer.

---

## 🗺️ Theory & Concepts

### The Core Trade-off

- Embedding (The "Speed" Path)
  - Nest child objects directly inside the parent document
  - Single-document atomicity: ACID at the document level, for free
  - No network round trips: One read returns parent + all children
  - Data locality: Parent and children stored physically together on disk
- Referencing (The "Scale" Path)
  - Store only an ID pointer (`user_id`, `order_id`) linking to a separate collection
  - Small, lean documents: No bloated parent docs
  - Independent updates: Change the child without rewriting the parent
  - Normalized source of truth: Change once, reflected everywhere

### Who Formalized It

- MongoDB Documentation
  - Formalizes "embed for 1:1 and 1:Few, reference for 1:Many and M:N"
  - Subset Pattern, Extended Reference, and Computed Pattern all originate here
- Rick Houlihan (AWS DynamoDB)
  - "Denormalize until it hurts, then denormalize some more"
  - DynamoDB's item collection model inherently favours embedding

### Critical Size Constraints

- MongoDB: BSON document limit = 16MB. Embedding that exceeds 16MB crashes the write
- DynamoDB: Item size limit = 400KB. Embedding large payloads forces splitting
- Couchbase: Document size limit = 20MB. Less constrained but still bounded
- Rule: If unbounded array growth is possible, DO NOT embed. Reference instead

### When Embedding Breaks

- Write contention: Every child update rewrites the entire parent document
- Array growth: An unbounded list (e.g., order history, message thread) grows the document toward the size limit
- Shared children: If a child belongs to multiple parents, embedding creates data duplication across parents

### When Referencing Breaks

- Application-side JOINs: The app must issue N+1 queries to resolve references
- No cross-document transactions (in some DBs): Updating parent and child separately can leave inconsistent state
- Read latency: Each reference adds a network round trip

---

## 🗺️ Techniques & Patterns

### T1: Pure Embedding (1:1 and 1:Few)

- When to use: Data is always read together. Child has no independent existence
- Examples
  - User → Profile (1:1): Profile is always loaded with user
  - Order → LineItems (<20 items): The entire order is loaded as one
  - Product → Specifications: Specs are always shown on the product page
- Mechanics
  - Single `get_item()` or `find_one()` returns the entire entity graph
  - Atomicity: Adding a line item to an order is an atomic document update
- Failure Mode
  - Embedding data that CHANGES independently. Example: Embedding full product details in every order. When product price changes, all historical orders show wrong price

### T2: Pure Referencing (1:Many Unbounded, M:N)

- When to use: Child count is unbounded, or child is shared across parents
- Examples
  - Post → Comments (unbounded): A viral post could have millions of comments
  - Student → Courses (M:N): Each student has many courses, each course has many students
  - User → Audit Log (append-only): Log entries only grow
- Mechanics
  - Parent stores no child data. Query children via their own partition/collection
  - Each child document has a `parent_id` field for the JOIN
- Failure Mode
  - N+1 query problem: Loading a post + 50 comments = 51 queries. Fix: batch-get or aggregation pipeline

### T3: Subset Pattern (Hybrid)

- When to use: You need the speed of embedding for the "hot" data but can't embed everything
- Mechanics
  - Embed the "Top 5" or "Latest 10" children in the parent
  - Reference the full collection in a separate collection for pagination/archive
  - Background job syncs the subset when new data arrives
- Example
  - Product document embeds `latest_5_reviews` for the product page
  - Full review collection referenced for "See all 2,340 reviews" pagination
- Failure Mode
  - Subset goes stale if the sync job fails. Detection: Compare count in subset vs full collection

### T4: Extended Reference Pattern

- When to use: You need display-only fields from a referenced entity without a full JOIN
- Mechanics
  - Embed only the fields needed for display (e.g., author name, avatar URL) in the parent
  - Reference the full entity for detail views
- Example
  - Blog post embeds `{author_name, author_avatar}` — no JOIN needed for the feed
  - "View author profile" link queries the full `authors` collection
- Failure Mode
  - Author changes their name. Embedded name is stale until a background sync runs
  - Mitigation: Use DynamoDB Streams / Change Streams to trigger sync on source update

### T5: Computed Pattern

- When to use: You need aggregated metrics (count, average, sum) without scanning all children
- Mechanics
  - Pre-compute the aggregate and embed in the parent: `{review_count: 2340, avg_rating: 4.2}`
  - Update via background job, Change Streams trigger, or transactional increment
- Example
  - Product document stores `review_count` and `avg_rating`
  - Adding a review triggers an atomic increment on the parent
- Failure Mode
  - Counter drift: If the increment job fails, the embedded count diverges from reality
  - Mitigation: Periodic reconciliation batch job that recomputes from source

### Cardinality Decision Matrix

- 1:1 → EMBED (always)
- 1:Few (<100) → EMBED (safe if child data is small and rarely updated independently)
- 1:Many (100 - 1,000) → IT DEPENDS (check: update frequency, document growth rate, read-together pattern)
- 1:Squillions (>10,000) → REFERENCE (embedding will blow past size limits)
- N:N → REFERENCE (embedding creates unmanageable duplication)

---

## 🗺️ Hands-On & Code

### MongoDB Embedding DDL

- User with embedded address: `{_id, name, email, address: {city, state, zip}}`
- Order with embedded line items: `{_id, order_id, items: [{product_id, name, qty, price}]}`
- Index on nested field: `db.users.createIndex({"address.city": 1})`

### MongoDB Referencing DDL

- Post: `{_id, author_id, title, body, created_at}`
- Comment: `{_id, post_id, author_id, body, created_at}`
- Application JOIN: `db.comments.find({post_id: "P-123"}).sort({created_at: -1}).limit(50)`

### DynamoDB Embedding

- Single item with nested map: `{PK: "USER#123", SK: "PROFILE", address: {city: "Seattle"}}`
- Item collection: Multiple items under same PK with different SK values (implicit embedding)

### Aggregation Pipeline for Reference Resolution

- MongoDB `$lookup`: Server-side JOIN between collections
- `db.posts.aggregate([{$lookup: {from: "comments", localField: "_id", foreignField: "post_id", as: "comments"}}])`
- Cost: Still a separate collection scan. Not a free JOIN — monitor explain plan

---

## 🗺️ Real-World Scenarios

### 01: LinkedIn News Feed — Subset Embedding

- The Setup: News feed shows post + latest 5 comments + like count inline
- Scale: 900M+ members, billions of feed impressions/day
- Design: Embed `{latest_5_comments, like_count, share_count}` in feed item. Full comments referenced separately
- Why It Works: 50 fewer network calls per feed scroll. P99 latency: <20ms for feed load

### 02: E-Commerce Order History — Full Embedding

- The Setup: Order page shows order metadata + all line items + shipping address
- Scale: Order has <50 items (bounded). Data is never updated after placement
- Design: Full embed. One GetItem returns the entire order page
- Why It Works: Order is immutable after creation. No write contention. Document stays under 100KB

### 03: Unbounded Array Incident — Checkout API Crash

- The Trap: E-commerce platform embedded full order history in customer document
- Scale: Power customers had 5,000+ orders. Document grew to 14MB
- What Broke: Approaching 16MB BSON limit. Customer profile reads took 500ms+ (entire 14MB transferred)
- The Fix: Moved order history to separate `orders` collection. Customer doc embeds only `last_5_orders` (Subset Pattern)
- Lesson: If cardinality is unbounded, ALWAYS reference

### 04: Stale Embedded Data — Author Name Change

- The Trap: Blog platform embedded author name + avatar in every post. Author changed name
- What Broke: 15,000 posts still showed old name. No sync mechanism existed
- The Fix: Added Change Stream listener on `authors` collection. On name update, batch-update all posts containing that author_id
- Lesson: If embedded data comes from a source that CAN change, you MUST have a sync mechanism

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Embedding Unbounded Lists

- Root Cause: Treating NoSQL as if documents can grow infinitely. No awareness of 16MB/400KB limits
- Diagnostic: Monitor document size distribution. Alert if P95 doc size crosses 50% of limit
- Correction: Any list that can grow beyond ~100 items must be referenced, not embedded

### M02: Referencing When Data Is Always Read Together

- Root Cause: Applying relational normalization habits. Separate collections for User and Profile
- Diagnostic: Count network round trips per API response. If >1 for a single-entity read, you're over-referencing
- Correction: Embed 1:1 and 1:Few relationships that are always fetched together

### M03: No Sync Mechanism for Embedded Copies

- Root Cause: Embedding denormalized data (author name, product price) without a background sync
- Diagnostic: Compare source-of-truth value vs embedded value for a sample. Any mismatch = no sync
- Correction: Implement Change Streams / DynamoDB Streams listener to propagate source updates to embedded copies

### M04: Using $lookup as a Primary Read Path

- Root Cause: Treating MongoDB `$lookup` as a free JOIN. It's not — it scans the foreign collection
- Diagnostic: Run `explain()` on aggregation pipeline. If $lookup stage shows full collection scan, it's expensive
- Correction: Embed data needed for the hot read path. Use $lookup only for infrequent or admin-facing queries

### M05: Ignoring Write Contention on Embedded Documents

- Root Cause: Multiple concurrent writers updating different children in the same parent document
- Diagnostic: High retry rate on write operations. Document-level lock contention metrics
- Correction: If children are updated independently and concurrently, reference them in separate documents

---

## 🗺️ Interview Angle

### Q1: How Would You Handle 10,000 Comments on a Single Post?

- What They Test: Do you know the embedding boundary?
- Principal Answer: Embed `latest_10_comments` in the post (Subset Pattern). Store full comment list in separate `comments` collection with PK=`post_id`. Paginate via sort on `created_at DESC`
- Follow-Up Trap: "What about like counts?" → Computed Pattern. Atomic increment on `like_count` field in the post document

### Q2: When Do You Choose Embedding Over Referencing?

- What They Test: Do you have a decision framework, not just intuition?
- Principal Answer: Cardinality matrix (1:1 → embed, 1:Squillions → reference). Plus three checks: read-together frequency, update independence, document growth rate. If all three favour embedding, embed. If any one fails, reference

### Whiteboard Blueprint

- The "Embedding vs Referencing Decision Tree": Start with cardinality → check read-together → check update frequency → check doc growth → decision (Embed / Reference / Hybrid)
- Draw the User document with embedded profile vs referenced orders — show the query difference (1 read vs N+1 reads)

---

## 🗺️ Assessment & Reflection

- For each collection in your current system: is the embedding bounded or unbounded?
- Do you have a sync mechanism for every piece of denormalized (embedded) data?
- How many of your read paths require application-side JOINs? Could any be eliminated with embedding?
- Have you hit the 16MB document limit? What was the root cause?
- Is your cardinality assessment documented, or does it only exist in tribal knowledge?
