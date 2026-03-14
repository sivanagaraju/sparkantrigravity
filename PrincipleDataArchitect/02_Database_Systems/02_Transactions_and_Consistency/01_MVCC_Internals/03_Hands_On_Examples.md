# MVCC Internals — Hands-On Examples

> Interrogating the hidden mechanics of MVCC in PostgreSQL and observing transaction isolation boundaries in real time.

---

## Example 1: Inspecting PostgreSQL Hidden MVCC Columns

PostgreSQL attaches hidden columns to every table to manage MVCC. You can query them directly to see MVCC in action.

```sql
-- 1. Create a test table
CREATE TABLE mvcc_test (id INT, value VARCHAR(50));

-- 2. Insert data and view hidden columns
INSERT INTO mvcc_test VALUES (1, 'Initial Value');

SELECT 
    id, 
    value, 
    xmin,  -- Transaction ID that inserted this row
    xmax,  -- Transaction ID that deleted/updated it (0 if live)
    cmin,  -- Command ID within transaction
    ctid   -- Physical location pointer (block, index)
FROM mvcc_test;

/* Output:
 id |      value      |   xmin   | xmax | cmin |  ctid
----+-----------------+----------+------+------+-------
  1 | Initial Value   | 1045231  |    0 |    0 | (0,1)
*/

-- 3. Update the record
UPDATE mvcc_test SET value = 'Updated Value' WHERE id = 1;

-- 4. Query again
SELECT id, value, xmin, xmax, ctid FROM mvcc_test;

/* Output reveals the new tuple. The old tuple is hidden but still exists on disk!
 id |      value      |   xmin   | xmax |  ctid
----+-----------------+----------+------+-------
  1 | Updated Value   | 1045232  |    0 | (0,2)   <-- New transaction ID, new physical location
*/
```

---

## Example 2: Using `pageinspect` to Find the "Ghost" Tuple

When we updated the row in Example 1, the original row didn't disappear—it was just marked with an `xmax` making it invisible. We can read raw disk pages to find it.

```sql
-- Install the page inspection tool
CREATE EXTENSION pageinspect;

-- Read the raw binary items from the first block (page 0) of our table
SELECT 
    lp AS line_pointer,
    t_xmin AS insert_tx,
    t_xmax AS delete_tx,
    t_ctid AS forwards_pointer,
    CASE WHEN (t_infomask & 256) > 0 THEN 'COMMITTED' ELSE 'PENDING' END as status
FROM heap_page_items(get_raw_page('mvcc_test', 0));

/* Output:
 line_pointer | insert_tx | delete_tx | forwards_pointer | status
--------------+-----------+-----------+------------------+-----------
            1 |   1045231 |   1045232 |            (0,2) | COMMITTED  <-- The dead "Ghost" tuple
            2 |   1045232 |         0 |            (0,2) | PENDING    <-- The live tuple
*/
```
**Takeaway**: You can literally see `delete_tx` (xmax) of row 1 pointing to the transaction that created row 2. The `forwards_pointer` (ctid) forms a linked list from the old version to the new version.

---

## Example 3: Simulating a Long-Running Read Blocking VACUUM

This is the most common MVCC production incident. Let's trigger it intentionally.

**Session A: (The Analyst)**
```sql
BEGIN REPEATABLE READ;
SELECT count(*) FROM mvcc_test;
-- Do not commit. Leave session open.
```

**Session B: (The Application workload)**
```sql
-- Generate 100,000 updates to the same row
DO $$
BEGIN
  FOR i IN 1..100000 LOOP
    UPDATE mvcc_test SET value = 'Update ' || i WHERE id = 1;
  END LOOP;
END;
$$;
```

**Session C: (The DBA investigating table bloat)**
```sql
-- Trigger manual cleanup
VACUUM VERBOSE mvcc_test;

/* Output:
INFO:  vacuuming "public.mvcc_test"
INFO:  "mvcc_test": found 0 removable, 100000 nonremovable row versions...
DETAIL:  100000 dead row versions cannot be removed yet, oldest xmin: 1045240
*/
```
**Takeaway**: Because **Session A** opened a transaction *before* the 100,000 updates happened, Session A's snapshot theoretically might need to inspect the old row versions. Therefore, `VACUUM` refuses to delete them. The table artificially balloons in size. 

Once you `COMMIT` or exit Session A, re-running `VACUUM` will successfully remove the 100,000 dead rows.

---

## Example 4: Write Amplification via Secondary Indexes (The Update Penalty)

Look at how an update behaves when you have secondary indexes in PostgreSQL versus MySQL.

```sql
-- Postgres Setup
CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR, last_login TIMESTAMP);
CREATE INDEX idx_name ON users(name);

INSERT INTO users (name, last_login) VALUES ('Alice', '2023-01-01');
```

If we run:
```sql
UPDATE users SET last_login = '2023-01-02' WHERE id = 1;
```

**In PostgreSQL (Append-Only):**
1. Physical row `(0, 1)` is marked deleted.
2. New physical row `(0, 2)` is created.
3. The Primary Key index is updated to point to `(0, 2)`.
4. **Write Amplification**: The `idx_name` index must ALSO be updated to point the key "Alice" to the new physical location `(0, 2)`, even though the `name` column was not modified! (Unless HOT updates successfully trigger, which only works if `(0,2)` fits on the exact same 8KB disk page as `(0,1)`).

**In MySQL/InnoDB (Undo logs + Clustered Index):**
1. The physical row is updated in place. Old data goes to Undo Log.
2. The Primary Key is untouched.
3. The `idx_name` index points to the logical PK (`1`), not a physical disk location.
4. **Therefore:** The `idx_name` index requires ZERO updates.

This structural difference has profound implications on schema design between the databases.
