# Further Reading: Upgrades & Migrations

## Essential Sources

*   **PostgreSQL Documentation — pg_upgrade**
    *   *Source:* postgresql.org/docs/current/pgupgrade.html
    *   *Why:* Official reference for pg_upgrade, including check mode, link mode, and post-upgrade steps.

*   **"Zero-downtime Postgres upgrades" — GitLab Engineering**
    *   *Source:* about.gitlab.com/blog
    *   *Why:* Detailed walkthrough of a real zero-downtime major version upgrade using logical replication at GitLab scale.

*   **"PostgreSQL at Scale: Database Schema Changes Without Downtime" — Braintree**
    *   *Source:* medium.com/paypal-tech
    *   *Why:* Practical guide to safe DDL deployment patterns from a payment processing company where downtime = lost revenue.

## Books

*   **Database Reliability Engineering — Laine Campbell & Charity Majors**
    *   *Why:* Chapter on schema management and upgrade strategies covers organizational processes and risk management.

*   **The Art of PostgreSQL — Dimitri Fontaine**
    *   *Why:* Covers advanced DDL patterns, online schema changes, and migration strategies specific to PostgreSQL.

## Tools

*   **pg_upgrade** — In-place PostgreSQL major version upgrade.
*   **Flyway** — Version-controlled database migration tool (Java, SQL-based).
*   **Alembic** — SQLAlchemy-based migration tool for Python projects.
*   **Liquibase** — Database-independent migration tool with XML/YAML/JSON changeset formats.
*   **gh-ost** — GitHub's online schema change tool for MySQL (triggerless).
*   **pt-online-schema-change** — Percona's online schema change tool for MySQL (trigger-based).
*   **pgLoader** — High-performance data migration tool (supports MySQL → PostgreSQL migration).
*   **pg_stat_statements** — Extension for tracking query performance (critical for post-upgrade validation).

## Cross-References

*   **WAL and Durability:** Major version upgrades require understanding WAL format changes. pg_upgrade handles this; logical replication bypasses it entirely.
*   **Replication Topologies:** pg_upgrade does not upgrade replicas; they must be rebuilt. Logical replication upgrade creates independent replicas for the new version.
*   **Connection Pooling:** During switchover, PgBouncer can pause client connections (`PAUSE` command) to prevent errors during the brief window when the backend changes.
*   **Backup & Recovery:** Always take a full backup BEFORE any upgrade or high-risk migration.
