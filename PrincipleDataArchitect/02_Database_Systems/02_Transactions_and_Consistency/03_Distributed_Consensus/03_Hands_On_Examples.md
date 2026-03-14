# Distributed Consensus — Hands-On Examples

> Every example here uses real tools and systems you can run locally. The goal is to build intuition by watching consensus happen — seeing leader elections, log replication, and failure recovery in real time.

---

## 1. Setting Up an etcd Cluster Locally

etcd is the most accessible Raft implementation to experiment with.

```bash
# Download etcd (macOS / Linux)
ETCD_VER=v3.5.12
curl -L https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz | tar xz

# Start a 3-node cluster
# Terminal 1 - Node 1
./etcd --name node1 \
  --initial-advertise-peer-urls http://127.0.0.1:2380 \
  --listen-peer-urls http://127.0.0.1:2380 \
  --listen-client-urls http://127.0.0.1:2379 \
  --advertise-client-urls http://127.0.0.1:2379 \
  --initial-cluster node1=http://127.0.0.1:2380,node2=http://127.0.0.1:2382,node3=http://127.0.0.1:2384 \
  --initial-cluster-state new

# Terminal 2 - Node 2
./etcd --name node2 \
  --initial-advertise-peer-urls http://127.0.0.1:2382 \
  --listen-peer-urls http://127.0.0.1:2382 \
  --listen-client-urls http://127.0.0.1:2381 \
  --advertise-client-urls http://127.0.0.1:2381 \
  --initial-cluster node1=http://127.0.0.1:2380,node2=http://127.0.0.1:2382,node3=http://127.0.0.1:2384 \
  --initial-cluster-state new

# Terminal 3 - Node 3
./etcd --name node3 \
  --initial-advertise-peer-urls http://127.0.0.1:2384 \
  --listen-peer-urls http://127.0.0.1:2384 \
  --listen-client-urls http://127.0.0.1:2383 \
  --advertise-client-urls http://127.0.0.1:2383 \
  --initial-cluster node1=http://127.0.0.1:2380,node2=http://127.0.0.1:2382,node3=http://127.0.0.1:2384 \
  --initial-cluster-state new
```

---

## 2. Observing Leader Election

```bash
# Check cluster health and identify the leader
etcdctl --endpoints=http://127.0.0.1:2379,http://127.0.0.1:2381,http://127.0.0.1:2383 \
  endpoint status --write-out=table

# Output:
# +----------------------------+------------------+---------+---------+...+----------+
# |          ENDPOINT          |        ID        | VERSION | DB SIZE |   | IS LEADER|
# +----------------------------+------------------+---------+---------+...+----------+
# | http://127.0.0.1:2379      | 8211f1d0f64f3269 |  3.5.12 |   20 kB |   |     true |
# | http://127.0.0.1:2381      | 91bc3c398fb3c146 |  3.5.12 |   20 kB |   |    false |
# | http://127.0.0.1:2383      | fd422379fda50e48 |  3.5.12 |   20 kB |   |    false |
# +----------------------------+------------------+---------+---------+...+----------+
```

### Forcing a Leader Election

```bash
# Kill the current leader (Ctrl+C on Node 1's terminal)
# Watch Node 2 or Node 3 logs — you'll see:
# "raft.node: ... elected leader ... at term 2"

# Verify the new leader
etcdctl --endpoints=http://127.0.0.1:2381,http://127.0.0.1:2383 \
  endpoint status --write-out=table

# Now one of the remaining nodes is the leader
# Node 1 is unreachable — but the cluster still works!
```

---

## 3. Proving Quorum Requirements

```bash
# With all 3 nodes running, write a key:
etcdctl --endpoints=http://127.0.0.1:2379 put mykey "hello"
# OK — quorum (2 of 3) available

# Kill Node 1 (the leader). New leader elected.
etcdctl --endpoints=http://127.0.0.1:2381 put mykey "world"
# OK — quorum (2 of 3) still available

# Now kill Node 2 as well. Only Node 3 remains.
etcdctl --endpoints=http://127.0.0.1:2383 put mykey "fail"
# Error: context deadline exceeded
# etcdserver: request timed out
# Cluster CANNOT serve writes — only 1 of 3 nodes available (no quorum)

# But reads might still work (depending on consistency mode):
etcdctl --endpoints=http://127.0.0.1:2383 get mykey --consistency=s
# "world" — stale read from local state (serializable, not linearizable)
```

---

## 4. Observing Log Replication

```bash
# Write a key through the leader
etcdctl --endpoints=http://127.0.0.1:2379 put counter "1"

# Read from each node — all should return the same value
etcdctl --endpoints=http://127.0.0.1:2379 get counter  # "1"
etcdctl --endpoints=http://127.0.0.1:2381 get counter  # "1"
etcdctl --endpoints=http://127.0.0.1:2383 get counter  # "1"

# Check the Raft log index on each node
etcdctl --endpoints=http://127.0.0.1:2379,http://127.0.0.1:2381,http://127.0.0.1:2383 \
  endpoint status --write-out=table
# The RAFT INDEX column should be identical (or very close) across all nodes
```

---

## 5. CockroachDB: Multi-Raft in Action

```bash
# Start a 3-node CockroachDB cluster locally
cockroach start --insecure --store=node1 --listen-addr=localhost:26257 \
  --http-addr=localhost:8080 --join=localhost:26257,localhost:26258,localhost:26259

cockroach start --insecure --store=node2 --listen-addr=localhost:26258 \
  --http-addr=localhost:8081 --join=localhost:26257,localhost:26258,localhost:26259

cockroach start --insecure --store=node3 --listen-addr=localhost:26259 \
  --http-addr=localhost:8082 --join=localhost:26257,localhost:26258,localhost:26259

# Initialize the cluster
cockroach init --insecure --host=localhost:26257
```

### Observing Range Distribution

```sql
-- Connect via SQL
cockroach sql --insecure --host=localhost:26257

-- Create a table and insert data
CREATE TABLE orders (id INT PRIMARY KEY, amount DECIMAL, customer TEXT);
INSERT INTO orders SELECT generate_series(1, 10000), random()*1000, 'customer_' || (random()*100)::INT;

-- See how ranges (Raft groups) are distributed
SELECT range_id, start_key, end_key, 
       lease_holder, replicas
FROM [SHOW RANGES FROM TABLE orders];

-- Each range has a lease holder (effectively the Raft leader for that range)
-- Replicas will be on all 3 nodes
```

### Simulating Node Failure

```sql
-- Kill node 3 (Ctrl+C)
-- Immediately run queries:
SELECT COUNT(*) FROM orders;
-- Still works! Quorum (2 of 3) available.

-- Check range health:
SELECT range_id, replicas, lease_holder
FROM crdb_internal.ranges
WHERE array_length(replicas, 1) < 3;
-- Shows under-replicated ranges
```

---

## 6. Python: Watching Consensus with etcd3 Client

```python
"""
Demonstrate consensus behavior with etcd3 client.
Run this while killing and restarting etcd nodes.
"""
import etcd3
import time
import threading

def watch_key(client, key):
    """Watch a key for changes — demonstrates log replication."""
    events_iterator, cancel = client.watch(key)
    for event in events_iterator:
        print(f"[WATCH] Key changed: {event.key.decode()} = {event.value.decode()}")

def demonstrate_linearizable_reads(endpoints):
    """Show that reads are linearizable by default."""
    clients = [etcd3.client(host='127.0.0.1', port=p) for p in endpoints]
    
    # Write through any node
    clients[0].put('test_key', 'value_1')
    
    # Read from all nodes — linearizable reads go to the leader
    for i, client in enumerate(clients):
        try:
            value, _ = client.get('test_key')
            print(f"Node {i}: {value.decode()}")
        except Exception as e:
            print(f"Node {i}: UNREACHABLE ({e})")

def demonstrate_lease_and_ttl(client):
    """Demonstrate distributed leases (built on consensus)."""
    # Create a lease (like a distributed TTL)
    lease = client.lease(ttl=10)  # 10-second TTL
    
    # Put a key with the lease
    client.put('session/user123', 'active', lease=lease)
    print("Session created with 10s TTL")
    
    # If this process dies, the key automatically expires
    # This is how distributed locks work — leader keeps refreshing the lease
    
    for i in range(12):
        value, _ = client.get('session/user123')
        if value:
            print(f"  t+{i}s: Session active ({value.decode()})")
            lease.refresh()  # Keep alive
        else:
            print(f"  t+{i}s: Session EXPIRED")
            break
        time.sleep(1)

if __name__ == '__main__':
    client = etcd3.client(host='127.0.0.1', port=2379)
    
    # Start watching in background
    watch_thread = threading.Thread(
        target=watch_key, args=(client, 'counter'), daemon=True
    )
    watch_thread.start()
    
    # Write values and observe replication
    for i in range(5):
        client.put('counter', str(i))
        print(f"Wrote counter={i}")
        time.sleep(1)
    
    demonstrate_linearizable_reads([2379, 2381, 2383])
    demonstrate_lease_and_ttl(client)
```

---

## 7. Raft Visualization Tool

The Raft protocol has an excellent interactive visualization:

```text
1. Go to: https://raft.github.io/
2. Click "Raft Visualization" 
3. You can:
   - Watch leader election in real time
   - Kill nodes and watch re-election
   - Send client requests and see log replication
   - Create network partitions and observe split-brain prevention
   - Speed up / slow down time to see timing effects

This is the BEST way to build intuition about Raft before 
any interview. Spend 30 minutes clicking through scenarios.
```

---

## 8. Before/After: Consensus Configuration Decisions

| Scenario | Wrong Choice | Right Choice | Why |
|---|---|---|---|
| 3-node cluster, one node slow | 5 nodes "for safety" | Investigate slow node, keep 3 | More nodes = slower writes. Fix the root cause. |
| Cross-datacenter cluster | 3 nodes across 3 DCs | 5 nodes (2+2+1) or 3 nodes (2+1) | Need quorum within reachable DCs during partition |
| etcd for Kubernetes | 1 node "for dev" | 3 nodes minimum in production | 1 node = zero fault tolerance. etcd failure = Kubernetes failure. |
| CockroachDB range size | 512MB ranges | 64MB (default) | Large ranges = more data to replicate during leader changes |
