# Hands-On Examples: Redis Sentinel & Cluster

## Scenario 1: Initializing and Managing a Sentinel Failover

### ❌ Before (Anti-Pattern: Hardcoded IPs)
Connecting an application directly to a standalone Redis IP.
```python
import redis
# When 10.0.1.5 dies, the app hard-crashes and requires a code deployment 
# to change the IP address to the replica.
client = redis.Redis(host='10.0.1.5', port=6379)
client.set("foo", "bar")
```

### ✅ After (Correct Approach: Sentinel Discovery)
The application connects to the Sentinel fleet instead. Sentinel dynamically provides the IP of whoever the current Master is.
```python
from redis.sentinel import Sentinel

# Connect to the 3-node Sentinel quorum
sentinel = Sentinel([
    ('10.0.1.10', 26379),
    ('10.0.1.11', 26379),
    ('10.0.1.12', 26379)
], socket_timeout=0.1)

# Request the master by its logical group name defined in sentinel.conf
# Sentinel queries its internal state and returns the correct IP dynamically.
master = sentinel.master_for('mymaster', socket_timeout=0.1)
master.set("foo", "bar") # Transparently hits 10.0.1.5

# Failover Simulator (Terminal)
# On the Redis Node: > redis-cli DEBUG SEGFAULT 
# Within 3 seconds, Sentinel promotes the replica. 
# The Python `master` object above automatically discovers the new IP (e.g. 10.0.1.6) 
# and resumes operations with only a momentary 3-second latency blip.
```

---

## Scenario 2: Connecting to Redis Cluster (The Smart Client)

Using a standard CLI tool against a Cluster will fail constantly as you hit nodes that don't own the assigned hash slot.

### Executing a manual GET on a Cluster
```bash
# Using standard redis-cli
$ redis-cli -h 10.0.1.1 -p 6379
10.0.1.1:6379> GET my_key
(error) MOVED 14315 10.0.1.3:6379

# You must add the -c (Cluster) flag to the CLI. 
# The CLI will now intercept the MOVED error and redirect automatically.
$ redis-cli -c -h 10.0.1.1 -p 6379
10.0.1.1:6379> GET my_key
-> Redirected to slot [14315] located at 10.0.1.3:6379
"value_here"
```

### Application Code (Smart Client)
If you don't use a Cluster-aware client in your application, you will suffer a 2x network latency penalty on every query because of constant `-MOVED` redirections. A Smart Client fetches the slot map (`CLUSTER SLOTS`) once on boot and caches it.

```python
from redis.cluster import RedisCluster

# You only need to provide 1 or 2 seed nodes. The client pulls the full map.
startup_nodes = [{"host": "10.0.1.1", "port": "6379"}]
rc = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

# The client hashes "my_key" internally, realizes it lives on 10.0.1.3,
# and opens a direct TCP connection exactly to 10.0.1.3. Zero redirections.
rc.set("my_key", "value")
```

---

## Scenario 3: Forcing Multi-Key Operations via Hash Tags

A massive limitation of Redis Cluster is the inability to run multi-key atomic transactions natively, because the nodes operate purely independently (Shared-Nothing).

### ❌ Before (Anti-Pattern)
Attempting a Lua script to atomically decrement inventory and update a ledger.
```python
# The keys explicitly hash to different nodes!
# inventory:item123 -> Hash Slot 4000 (Master A)
# ledger:item123 -> Hash Slot 12000 (Master B)

rc.eval(lua_script, 2, "inventory:item123", "ledger:item123", "1")
# Result: CROSSSLOT Keys in request don't hash to the same slot
```

### ✅ After (Correct Approach)
Using Hash Tags `{}` to artificially manipulate the CRC16 hash curve. Note that the string outside the braces is entirely ignored during the mathematical modulo phase.

```python
# Both keys use {item123} as the exclusive hashing entity.
# {item123} hashes to exactly Slot 8421.
# Both strings are physically routed to the exact same Master C.

rc.eval(lua_script, 2, "inventory:{item123}", "ledger:{item123}", "1")
# Result: OK (Script executes atomically on Master C with zero 2-Phase Commit overhead).
```

---

## Maintenance Scenario: Adding a Node to a Live Cluster

Redis Cluster supports live scaling. When you launch a new Master node, it arrives completely empty (owning 0 Hash Slots). You must explicitly reshard.

```bash
# 1. Join the empty node to the existing cluster
redis-cli --cluster add-node 10.0.1.4:6379 10.0.1.1:6379

# 2. Trigger a live reshard (Interactive Wizard)
redis-cli --cluster reshard 10.0.1.1:6379
# Prompts:
# How many slots do you want to move (from 1 to 16384)? 
> 4096  (Moving exactly 25% of the cluster to the new 4th node)
# What is the receiving node ID? 
> <Node_ID_of_10.0.1.4>
# Source node #1: 
> all
```
**Mechanism Under the Hood**: Redis begins moving keys. During this 5-minute process, if a client requests a key that is currently in transit, the old Master replies with an `-ASK` redirection. The client seamlessly hops to the new node to fetch the key. No data is locked, and no downtime occurs.
