# Query-Driven Modeling — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Normalizing in NoSQL (Relational Thinking)

**The mistake**: Designing DynamoDB/Cassandra tables as if they were relational — separate tables for users, orders, and items with foreign keys and no denormalization.

```python
# ❌ WRONG: Three separate DynamoDB tables, need to "JOIN" in application
user = users_table.get_item(Key={'user_id': '123'})
orders = orders_table.query(KeyConditionExpression=Key('user_id').eq('123'))
for order in orders['Items']:
    items = items_table.query(KeyConditionExpression=Key('order_id').eq(order['order_id']))
# 3 round trips to DynamoDB. 15-30ms total. Defeats the purpose.
```

**What breaks**: NoSQL databases don't support JOINs. If you normalize, every read requires multiple round trips to different tables. Latency multiplies with each hop.

**Fix**: Denormalize into a single table:

```python
# ✅ CORRECT: One query, one partition, all data
response = table.query(KeyConditionExpression=Key('PK').eq(f'USER#123'))
# Returns: PROFILE + ORDER#ts1 + ORDER#ts2 + ... all in one round trip. 3ms.
```

---

## Anti-Pattern 2: Low-Cardinality Partition Keys (Hot Partitions)

**The mistake**: Choosing a partition key with few distinct values (status, date, country). All traffic concentrates on a few partitions.

**Detection**: DynamoDB CloudWatch metric `ConsumedReadCapacityUnits` shows spikes on specific partitions. Cassandra `nodetool tablestats` shows uneven compaction.

**Fix**: Use high-cardinality keys. If you need to query by low-cardinality attribute, use a GSI:

```python
# ❌ WRONG: PK = order_status ("PENDING", "SHIPPED", "DELIVERED")
# 3 partitions for millions of orders

# ✅ CORRECT: PK = order_id (high cardinality)
# Use GSI for status-based queries:
# GSI PK = STATUS#PENDING, SK = timestamp
```

---

## Anti-Pattern 3: Scan Instead of Query

**The mistake**: Using `Scan` to find items when a proper key design would enable `Query`.

```python
# ❌ WRONG: Scan entire table to find orders by status
response = table.scan(
    FilterExpression=Attr('status').eq('PENDING')
)
# Reads EVERY item in the table, then filters. Cost: O(n). Latency: 10s+.
```

**Fix**: Design a GSI for the access pattern:

```python
# ✅ CORRECT: Query GSI designed for status lookup
response = table.query(
    IndexName='GSI-Status',
    KeyConditionExpression=Key('GSI2PK').eq('STATUS#PENDING'),
    Limit=50
)
# Reads only matching items. Cost: O(result_size). Latency: <5ms.
```

---

## Anti-Pattern 4: Unbounded Partition Growth

**The mistake**: Using a partition key that accumulates unbounded data over time (e.g., `channel_id` for messages).

**What breaks**: A partition grows from KB to GB over months/years. Cassandra partitions >100MB degrade read performance. DynamoDB item collections >10GB hit the limit.

**Fix**: Time-bucket the partition key:

```python
# ❌ WRONG: PK = channel_id (unbounded — grows forever)
# ✅ CORRECT: PK = channel_id#2024-03 (monthly bucket)
# "Load channel" queries the current bucket. Older buckets accessed on scroll-back.
```

---

## Anti-Pattern 5: Designing Without an Access Pattern Document

**The mistake**: Starting to write code and create tables before enumerating all access patterns. You discover a missing access pattern in production and can't serve it without a table redesign.

**Fix**: Create an access pattern table before writing any code:

| # | Access Pattern | Operation | PK | SK | Index | Latency SLA |
|---|---|---|---|---|---|---|
| AP1 | Get user | Read | USER#id | PROFILE | Table | <5ms |
| AP2 | User by email | Read | email | — | GSI1 | <5ms |
| AP3 | User's orders | Read | USER#id | ORDER#ts | Table | <10ms |
| AP4 | Update status | Write | ORDER#id | METADATA | Table | <5ms |

This document is the contract between the data architect, the developer, and the product manager.

---

## Decision Matrix — When Query-Driven Modeling Is the WRONG Choice

| Scenario | Why It's Wrong | Better Alternative |
|---|---|---|
| Ad-hoc analytics (unknown queries) | Can't pre-design for unknown patterns | Data warehouse (Redshift, BigQuery) |
| Complex relationships (many-to-many) | Denormalization explodes; graph is better | Graph database or relational |
| Rapidly changing access patterns | Each change requires schema migration | Flexible document store or relational |
| Small dataset (<100K rows) | Over-engineering; PostgreSQL is fine | PostgreSQL |
| Strong consistency across entities | NoSQL prefers eventual consistency | Relational database |
