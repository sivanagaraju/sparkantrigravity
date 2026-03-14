# Data Distribution Mechanics — Hands-On Examples

## Integration Diagram: Connecting Data Distribution with Streaming

When using highly distributed databases (e.g., Cassandra), ingesting data efficiently requires a distributed messaging layer like Kafka to prevent overwhelming any single coordinator node.

```mermaid
graph LR
    subgraph "Streaming Ingestion Layer"
        P[Producers] -->|Publish| K[Kafka Topic (Partitioned)]
        K --> C1[Kafka Consumer Group 1]
        K --> C2[Kafka Consumer Group 2]
    end
    
    subgraph "Distributed Database Layer"
        C1 -->|Batch Write| R1[Coordinator Node A]
        C2 -->|Batch Write| R2[Coordinator Node B]
        
        R1 -.->|Hash Routing| DB1[(Storage Node 1)]
        R1 -.->|Hash Routing| DB2[(Storage Node 2)]
        R2 -.->|Hash Routing| DB2
        R2 -.->|Hash Routing| DB3[(Storage Node 3)]
    end
```

## Before vs After: Fixing the "Monotonic Insert" Hotspot

One of the most common early-career mistakes in distributed databases is using an auto-incrementing ID or a standard timestamp as a primary/partition key. In a range-partitioned database, this funnels 100% of all new writes to the single node holding the "latest" range.

**Before: The Hotspot (CockroachDB/Spanner)**
```sql
-- DANGEROUS: All inserts hit a single range because the sequence is monotonically increasing.
CREATE TABLE orders_bad (
    order_id SERIAL PRIMARY KEY,
    customer_id INT,
    amount DECIMAL,
    created_at TIMESTAMP
);
```

**After: Hash-Prefixing or UUIDv4**
```sql
-- PRINCIPAL FIX: Use UUIDv4 which scatters writes uniformly across all ranges.
CREATE TABLE orders_good (
    order_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id INT,
    amount DECIMAL,
    created_at TIMESTAMP
);

-- ALTERNATIVE FIX (If sequential IDs are absolutely required): Hash-prefixing
-- Prepend a hash of the ID to visually distribute the keyspace.
CREATE TABLE orders_hash_prefix (
    shard_id INT AS (order_id % 16) VIRTUAL,
    order_id SERIAL,
    customer_id INT,
    PRIMARY KEY (shard_id, order_id)
);
```

## Code Example: PostgreSQL Declarative Partitioning

Even in single-node databases, partitioning principles apply up to the limits of the hardware. This is standard practice before moving to a fully distributed NewSQL system.

```sql
-- 1. Create the parent partitioned table
CREATE TABLE telemetry (
    device_id UUID NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    temperature NUMERIC,
    humidity NUMERIC
) PARTITION BY RANGE (recorded_at);

-- 2. Create the partitions (ranges)
CREATE TABLE telemetry_2024_01 PARTITION OF telemetry
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE telemetry_2024_02 PARTITION OF telemetry
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 3. Add an index to each partition automatically via the parent
CREATE INDEX idx_telemetry_device ON telemetry (device_id);
```

## Configuration: DynamoDB Sharding Under the Hood

You don't write DDL for DynamoDB partitions. Instead, AWS allocates a "Partition" for every `1,000 WCUs` (Write Capacity Units) or `3,000 RCUs`, or `10GB` of data. 

**Infrastructure as Code (Terraform):**
```hcl
resource "aws_dynamodb_table" "user_sessions" {
  name           = "UserSessions"
  billing_mode   = "PROVISIONED"
  # This provisions 10,000 WCU. DynamoDB will implicitly create at least 10 physical partitions behind the scenes (10,000 / 1,000).
  read_capacity  = 10000 
  write_capacity = 10000 
  hash_key       = "SessionId"

  attribute {
    name = "SessionId"
    type = "S"
  }
}
```

## Runnable Exercise

**Simulate Consistent Hashing in Python**

To truly internalize data distribution, write the hash ring logic.

```python
import hashlib
import bisect

class HashRing:
    def __init__(self, nodes, replicas=3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        
        for node in nodes:
            self.add_node(node)

    def _hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.replicas):
            virtual_node_key = f"{node}_v{i}"
            hashed_key = self._hash(virtual_node_key)
            self.ring[hashed_key] = node
            bisect.insort(self.sorted_keys, hashed_key)

    def get_node(self, string_key):
        if not self.ring:
            return None
        hashed_key = self._hash(string_key)
        idx = bisect.bisect(self.sorted_keys, hashed_key)
        # Wrap around the ring
        if idx == len(self.sorted_keys):
            idx = 0
        return self.ring[self.sorted_keys[idx]]

# Usage:
ring = HashRing(["NodeA", "NodeB", "NodeC"], replicas=10)
print(f"User 123 routes to: {ring.get_node('user_123')}")
print(f"User 456 routes to: {ring.get_node('user_456')}")
```
