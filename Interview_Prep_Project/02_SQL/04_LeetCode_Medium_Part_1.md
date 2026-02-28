# LeetCode SQL Medium - Part 1 (Questions 1-10)

LeetCode Medium SQL questions with T-SQL solutions.

---

## Q1: Second Highest Salary

### Tables

```
Employee (id INT PK, salary INT)
```

### Problem

Find the second highest **distinct** salary. Return NULL if no second highest exists.

### Hint

Use DENSE_RANK or handle with CASE WHEN for NULL scenario.

### Understanding the Problem

- Need **distinct** salaries (100, 100, 200 → only 100 and 200)
- Second highest means rank 2 after sorting DESC
- If only one distinct salary exists, return NULL (not empty)

### Solution Approach

1. Use DENSE_RANK to rank distinct salaries
2. Use CASE WHEN + MAX to return NULL if no rank 2 exists

### T-SQL Answer

```sql
WITH RankedSalaries AS (
    SELECT salary,
           DENSE_RANK() OVER (ORDER BY salary DESC) AS rn
    FROM Employee
)
SELECT MAX(CASE WHEN rn = 2 THEN salary ELSE NULL END) AS SecondHighestSalary
FROM RankedSalaries;
```

### Why This Approach?

- `DENSE_RANK` handles duplicates (same salary = same rank)
- `MAX(CASE WHEN...)` returns NULL when no rank 2 exists (vs empty result)
- Single pass through data

### Alternative Approaches

**Using OFFSET-FETCH:**

```sql
SELECT MAX(salary) AS SecondHighestSalary
FROM (
    SELECT DISTINCT salary
    FROM Employee
    ORDER BY salary DESC
    OFFSET 1 ROW FETCH NEXT 1 ROW ONLY
) t;
```

### Common Mistakes

- Using ROW_NUMBER (gives 1,2,3 even for same salaries)
- Returning empty result instead of NULL

---

## Q2: Nth Highest Salary

### Tables

```
Employee (id INT PK, salary INT)
```

### Problem

Write a function to get the Nth highest distinct salary. Return NULL if less than N distinct salaries.

### Hint

Same as Q1 but with parameter N.

### Understanding the Problem

- Parameterized version of Q1
- N=2 is second highest, N=1 is highest

### T-SQL Answer

```sql
CREATE FUNCTION getNthHighestSalary(@N INT) RETURNS INT AS
BEGIN
    RETURN (
        SELECT MAX(CASE WHEN rn = @N THEN salary ELSE NULL END)
        FROM (
            SELECT salary,
                   DENSE_RANK() OVER (ORDER BY salary DESC) AS rn
            FROM Employee
        ) t
    );
END
```

### Why This Approach?

- Same logic as Q1, just parameterized
- Function wrapper required by LeetCode

---

## Q3: Rank Scores

### Tables

```
Scores (id INT PK, score DECIMAL(3,2))
```

### Problem

Rank scores from highest to lowest. Same scores get same rank. No gaps in ranking.

### Hint

DENSE_RANK is exactly this - same values get same rank, no gaps.

### Understanding the Problem

- Highest = rank 1
- Ties get same rank
- Next rank is consecutive (no gaps like RANK would give)

### T-SQL Answer

```sql
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS rank
FROM Scores;
```

### Why This Approach?

- `DENSE_RANK` = same rank for ties, no gaps
- `RANK` would skip numbers after ties (1,1,3 instead of 1,1,2)
- `ROW_NUMBER` would give unique numbers (1,2,3)

### Common Mistakes

- Using RANK instead of DENSE_RANK (creates gaps)
- Forgetting DESC order

---

## Q4: Consecutive Numbers

### Tables

```
Logs (id INT PK AUTO_INCREMENT, num INT)
```

### Problem

Find numbers that appear at least 3 times consecutively.

### Hint

Use LAG/LEAD to compare with previous and next values.

### Understanding the Problem

- ID is auto-increment (1,2,3,4...)
- Need same number in 3 consecutive rows
- Return distinct numbers

### Solution Approach

1. Get previous value with LAG
2. Get next value with LEAD
3. Filter where current = previous = next

### T-SQL Answer

```sql
WITH ConsecutiveCheck AS (
    SELECT num,
           LAG(num) OVER (ORDER BY id) AS prev_num,
           LEAD(num) OVER (ORDER BY id) AS next_num
    FROM Logs
)
SELECT DISTINCT num AS ConsecutiveNums
FROM ConsecutiveCheck
WHERE num = prev_num AND num = next_num;
```

### Why This Approach?

- LAG/LEAD access adjacent rows without self-join
- DISTINCT handles cases where 4+ consecutive (would match multiple times)

### Alternative Approaches

**Self-join (older approach):**

```sql
SELECT DISTINCT l1.num AS ConsecutiveNums
FROM Logs l1
JOIN Logs l2 ON l1.id = l2.id - 1
JOIN Logs l3 ON l2.id = l3.id - 1
WHERE l1.num = l2.num AND l2.num = l3.num;
```

---

## Q5: Department Highest Salary

### Tables

```
Employee (id INT PK, name VARCHAR, salary INT, departmentId INT FK)
Department (id INT PK, name VARCHAR)
```

### Problem

Find employees with highest salary in each department. Multiple employees can tie.

### Hint

RANK within each department, then filter rank = 1.

### Understanding the Problem

- Partition by department
- Rank by salary DESC
- If tie, both get rank 1

### T-SQL Answer

```sql
WITH RankedEmployees AS (
    SELECT d.name AS Department,
           e.name AS Employee,
           e.salary AS Salary,
           RANK() OVER (PARTITION BY e.departmentId ORDER BY e.salary DESC) AS rn
    FROM Employee e
    INNER JOIN Department d ON e.departmentId = d.id
)
SELECT Department, Employee, Salary
FROM RankedEmployees
WHERE rn = 1;
```

### Why This Approach?

- PARTITION BY separates ranking per department
- RANK (not ROW_NUMBER) allows ties
- JOIN gets department name

---

## Q6: Game Play Analysis IV

### Tables

```
Activity (player_id INT, device_id INT, event_date DATE, games_played INT)
PK: (player_id, event_date)
```

### Problem

Find fraction of players who logged in the day after their first login.

### Hint

Find first login date per player, then check if day+1 exists.

### Understanding the Problem

- First login = MIN(event_date) per player
- Check if that player has event_date = first_date + 1
- Calculate: (players with day-after login) / (total players)

### T-SQL Answer

```sql
WITH FirstLogin AS (
    SELECT player_id, MIN(event_date) AS first_date
    FROM Activity
    GROUP BY player_id
)
SELECT ROUND(
    1.0 * COUNT(DISTINCT a.player_id) / (SELECT COUNT(DISTINCT player_id) FROM Activity),
    2
) AS fraction
FROM FirstLogin f
INNER JOIN Activity a ON f.player_id = a.player_id
    AND a.event_date = DATEADD(DAY, 1, f.first_date);
```

### Why This Approach?

- CTE gets first login per player
- JOIN back finds players with next-day activity
- Division gives fraction

---

## Q7: Managers with at Least 5 Direct Reports

### Tables

```
Employee (id INT PK, name VARCHAR, department VARCHAR, managerId INT)
```

### Problem

Find managers with at least 5 direct reports.

### Hint

GROUP BY managerId, HAVING COUNT >= 5, then get name.

### Understanding the Problem

- managerId points to this employee's manager
- Count employees per managerId
- Filter for 5+

### T-SQL Answer

```sql
SELECT e.name
FROM Employee e
WHERE e.id IN (
    SELECT managerId
    FROM Employee
    GROUP BY managerId
    HAVING COUNT(*) >= 5
);
```

### Why This Approach?

- Subquery finds manager IDs with 5+ reports
- Outer query gets their names

### Alternative Approaches

**Using JOIN:**

```sql
WITH ManagerCounts AS (
    SELECT managerId, COUNT(*) AS cnt
    FROM Employee
    GROUP BY managerId
    HAVING COUNT(*) >= 5
)
SELECT e.name
FROM Employee e
INNER JOIN ManagerCounts m ON e.id = m.managerId;
```

---

## Q8: Investments in 2016

### Tables

```
Insurance (pid INT PK, tiv_2015 FLOAT, tiv_2016 FLOAT, lat FLOAT, lon FLOAT)
```

### Problem

Sum of tiv_2016 for policyholders who:

1. Have same tiv_2015 as at least one other policyholder
2. Have unique (lat, lon) - no one else at same location

### Hint

Find duplicate tiv_2015 values. Find unique lat/lon pairs.

### T-SQL Answer

```sql
WITH DupeTIV AS (
    SELECT tiv_2015
    FROM Insurance
    GROUP BY tiv_2015
    HAVING COUNT(*) > 1
),
UniqueLocation AS (
    SELECT lat, lon
    FROM Insurance
    GROUP BY lat, lon
    HAVING COUNT(*) = 1
)
SELECT ROUND(SUM(i.tiv_2016), 2) AS tiv_2016
FROM Insurance i
INNER JOIN DupeTIV d ON i.tiv_2015 = d.tiv_2015
INNER JOIN UniqueLocation u ON i.lat = u.lat AND i.lon = u.lon;
```

### Why This Approach?

- Two CTEs filter the two conditions
- JOIN ensures both conditions met

---

## Q9: Friend Requests II - Who Has the Most Friends

### Tables

```
RequestAccepted (requester_id INT, accepter_id INT, accept_date DATE)
PK: (requester_id, accepter_id)
```

### Problem

Find the person with most friends and count. Friendship is mutual.

### Hint

UNION ALL requester and accepter columns, then count.

### Understanding the Problem

- If A requested B and B accepted, both are friends
- Count appearances in both columns combined

### T-SQL Answer

```sql
WITH AllFriends AS (
    SELECT requester_id AS id FROM RequestAccepted
    UNION ALL
    SELECT accepter_id AS id FROM RequestAccepted
)
SELECT TOP 1 id, COUNT(*) AS num
FROM AllFriends
GROUP BY id
ORDER BY num DESC;
```

### Why This Approach?

- UNION ALL combines both sides of friendship
- Each appearance = one friend
- TOP 1 gets the winner

---

## Q10: Tree Node

### Tables

```
Tree (id INT PK, p_id INT)  -- p_id is parent id
```

### Problem

Label each node as: Root (no parent), Leaf (no children), Inner (has both).

### Hint

CASE WHEN with subquery to check if id appears as p_id.

### Understanding the Problem

- Root: p_id IS NULL
- Leaf: id NOT IN (SELECT p_id FROM Tree)
- Inner: has parent AND is parent of someone

### T-SQL Answer

```sql
SELECT id,
       CASE 
           WHEN p_id IS NULL THEN 'Root'
           WHEN id IN (SELECT p_id FROM Tree WHERE p_id IS NOT NULL) THEN 'Inner'
           ELSE 'Leaf'
       END AS type
FROM Tree;
```

### Why This Approach?

- Check conditions in order: Root first (NULL parent)
- Then check if appears as parent (Inner)
- Everything else is Leaf

---

## Summary: Key Window Functions

| Function | Use Case |
|----------|----------|
| `ROW_NUMBER()` | Unique sequential numbers |
| `RANK()` | Same value = same rank, gaps after ties |
| `DENSE_RANK()` | Same value = same rank, no gaps |
| `LAG(col, n)` | Get value from n rows before |
| `LEAD(col, n)` | Get value from n rows after |
