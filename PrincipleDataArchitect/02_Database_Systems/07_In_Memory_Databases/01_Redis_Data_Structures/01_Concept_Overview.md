# Redis Data Structures — Concept Overview

> Not just a cache: Strings, Hashes, Lists, Sets, Sorted Sets, Streams, and HyperLogLog.

## Data Structure Decision Matrix

| Structure | Use Case | Time Complexity | Example |
|---|---|---|---|
| **String** | Cache, counters, session tokens | O(1) get/set | `SET session:abc123 "user_data"` |
| **Hash** | Object storage (user profile) | O(1) per field | `HSET user:1 name "Alice" email "a@b.com"` |
| **List** | Queue, recent activity feed | O(1) push/pop | `LPUSH queue:tasks "task_json"` |
| **Set** | Unique tags, online users | O(1) add/member | `SADD online_users "user:123"` |
| **Sorted Set** | Leaderboards, rate limiting | O(log n) add | `ZADD leaderboard 1500 "player:1"` |
| **Stream** | Event log, message queue | O(1) append | `XADD events * type "click" page "/home"` |
| **HyperLogLog** | Unique visitor counting (approx) | O(1) | `PFADD daily_visitors "ip:1.2.3.4"` |

## War Story: Twitter — Redis Sorted Sets for Timelines

Twitter uses Redis Sorted Sets for user timelines. Each tweet ID is a member with the timestamp as the score. `ZRANGEBYSCORE timeline:user123 -inf +inf LIMIT 0 20` returns the latest 20 tweets in O(log n + k) time, regardless of total timeline length.

## References

| Resource | Link |
|---|---|
| [Redis Data Types](https://redis.io/docs/data-types/) | Official documentation |
| Cross-ref: Redis Cluster | [../04_Redis_Cluster_And_Sentinel](../04_Redis_Cluster_And_Sentinel/) |
