# Upgrades and Migrations — Concept Overview

> Zero-downtime database upgrades: the hardest operational challenge in data engineering.

---

## Upgrade Strategies

| Strategy | Downtime | Complexity | Risk |
|---|---|---|---|
| **pg_upgrade (in-place)** | Minutes (catalog rewrite) | Low | Medium |
| **Logical replication** | Near-zero | High | Low |
| **Blue-green with DNS switch** | Seconds | Medium | Low |
| **Dump and restore** | Hours (for large DBs) | Low | High (long outage) |

## War Story: Stripe — Zero-Downtime PostgreSQL Major Version Upgrade

Stripe upgraded PostgreSQL from 9.6 to 14 on their payments database (petabyte-scale) using logical replication: set up a new cluster on PG14, stream changes via logical decoding, validate data consistency, then DNS cutover in <5 seconds. Total preparation: 3 months. Actual downtime: 4 seconds.

## References

| Resource | Link |
|---|---|
| [pg_upgrade](https://www.postgresql.org/docs/current/pgupgrade.html) | Official docs |
| [Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html) | For migration |
