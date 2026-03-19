# Hands-On Examples: Graph Databases

## 1. Cypher Basics: Nodes, Relationships, and Constraints

Unlike SQL which declares tables, Cypher operates entirely on patterns drawn with ASCII-art style syntax: `(node)-[:REL]->(node)`. Here we create schemas and insert data.

```cypher
-- 1. Create constraints to ensure data integrity and create underlying B-Tree indexes
-- Essential for the "Anchor Phase" of a graph traversal.
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT bank_acct_unique IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.account_num IS UNIQUE;

-- 2. Create the topology in a single transaction
-- We create explicit nodes, and connect them with typed, directed edges.
MERGE (u1:User {id: "U-100", name: "Alice", risk_score: 0.1})
MERGE (u2:User {id: "U-101", name: "Bob", risk_score: 0.8})
MERGE (b1:BankAccount {account_num: "ACC-1111", bank: "Chase"})
MERGE (b2:BankAccount {account_num: "ACC-2222", bank: "Citi"})

-- Create relationships (edges) which can hold their own properties
MERGE (u1)-[:OWNS {since: "2023-01-01"}]->(b1)
MERGE (u2)-[:OWNS {since: "2023-05-12"}]->(b2)
MERGE (b1)-[:TRANSFERRED_TO {amount: 50000, date: "2024-03-01"}]->(b2);
```

## 2. Advanced Cypher: Multi-Hop Fraud Ring Detection

This solves the famous "Cartesian Explosion" problem of RDBMS joins. We want to find cases where Alice sent money to an account owned by someone else, who then immediately sent money to *another* account that is eventually owned back by Alice (circular laundering).

```cypher
-- Match a pattern up to 5 hops deep
MATCH path = (startAccount:BankAccount)-[:TRANSFERRED_TO*1..5]->(endAccount:BankAccount)
WHERE startAccount.account_num = "ACC-1111"

-- Validate the structural loop
AND startAccount <> endAccount
AND (endAccount)-[:TRANSFERRED_TO]->(startAccount) 

-- Analytics: Unpack the paths
WITH path, 
     relationships(path) AS transfers, 
     nodes(path) AS accounts
     
-- Sum the total volume laundered in this ring
RETURN accounts, 
       reduce(total = 0, t IN transfers | total + t.amount) AS total_laundered_volume
ORDER BY total_laundered_volume DESC
LIMIT 10;
```
*Note: The `*1..5` specifies variable-length expansion. In a graph DB, this requires milliseconds. In PostgreSQL, this requires complex Recursive CTEs and minutes of execution time.*

## 3. Integration Diagram: Feeding the Graph via CDC

Graph DBs are often downstream analytic engines fed by application databases.

```mermaid
graph TD
    App(Banking App) --> Postgres[(Primary Ledger)]
    Postgres -- WAL / Binlog --> Debezium[Debezium CDC]
    Debezium --> Kafka[Kafka Topics <br/> 'users', 'transfers']
    
    Kafka --> Faust[Stream Processor <br/> Flink/Faust]
    Note over Faust: Transform tabular CDC <br/> into Graph Nodes & Edges
    
    Faust -- Cypher `UNWIND` API --> Neo4j[(Neo4j Graph Cluster)]
    
    FraudDef[Fraud Service] -- Cypher Query --> Neo4j
```

## Before vs. After: Resolving Complex Hierarchies

**Bad Approach: RDBMS (PostgreSQL)**
To find all sub-departments beneath "Engineering" (which has unbounded depth):
```sql
WITH RECURSIVE dept_tree AS (
    SELECT id, name, parent_id
    FROM departments
    WHERE name = 'Engineering'
  UNION ALL
    SELECT d.id, d.name, d.parent_id
    FROM departments d
    INNER JOIN dept_tree dt ON dt.id = d.parent_id
)
SELECT * FROM dept_tree;
```
*Why it fails:* Recursive CTEs must build massive temporary tables repeatedly. Highly memory intensive, completely unpredictable latency at scale.

**Correct Approach: Graph Database (Cypher)**
```cypher
MATCH (parent:Department {name: 'Engineering'})-[:HAS_SUBDEPT*]->(child:Department)
RETURN child;
```
*Why it wins:* It locates the "Engineering" anchor node, then strictly follows pointers. Constant time per hop. Zero table scans.
