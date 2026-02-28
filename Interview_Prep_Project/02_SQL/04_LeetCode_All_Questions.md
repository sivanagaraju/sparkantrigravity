# LeetCode SQL Medium - All Questions (Quick Reference)

All 19 LeetCode Medium SQL questions with T-SQL solutions.

---

## Q1: Second Highest Salary

**Tables**: Employee (id, salary) | **Key**: DENSE_RANK, NULL handling

```sql
WITH CTE AS (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rn FROM Employee
)
SELECT MAX(CASE WHEN rn = 2 THEN salary END) AS SecondHighestSalary FROM CTE;
```

---

## Q2: Nth Highest Salary

**Tables**: Employee | **Key**: Same as Q1, parameterized

```sql
CREATE FUNCTION getNthHighestSalary(@N INT) RETURNS INT AS BEGIN
    RETURN (SELECT MAX(CASE WHEN rn = @N THEN salary END) FROM 
        (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rn FROM Employee) t);
END
```

---

## Q3: Rank Scores

**Tables**: Scores (id, score) | **Key**: DENSE_RANK for no gaps

```sql
SELECT score, DENSE_RANK() OVER (ORDER BY score DESC) AS rank FROM Scores;
```

---

## Q4: Consecutive Numbers

**Tables**: Logs (id, num) | **Key**: LAG/LEAD for adjacent rows

```sql
WITH CTE AS (
    SELECT num, LAG(num) OVER (ORDER BY id) AS prev, LEAD(num) OVER (ORDER BY id) AS next FROM Logs
)
SELECT DISTINCT num AS ConsecutiveNums FROM CTE WHERE num = prev AND num = next;
```

---

## Q5: Department Highest Salary

**Tables**: Employee, Department | **Key**: RANK + PARTITION BY

```sql
WITH CTE AS (
    SELECT d.name Dept, e.name Emp, e.salary, RANK() OVER (PARTITION BY e.departmentId ORDER BY salary DESC) rn
    FROM Employee e JOIN Department d ON e.departmentId = d.id
)
SELECT Dept Department, Emp Employee, salary Salary FROM CTE WHERE rn = 1;
```

---

## Q6: Game Play Analysis IV

**Tables**: Activity (player_id, event_date) | **Key**: MIN date + DATEADD

```sql
WITH First AS (SELECT player_id, MIN(event_date) fd FROM Activity GROUP BY player_id)
SELECT ROUND(1.0 * COUNT(DISTINCT a.player_id) / (SELECT COUNT(DISTINCT player_id) FROM Activity), 2) fraction
FROM First f JOIN Activity a ON f.player_id = a.player_id AND a.event_date = DATEADD(DAY, 1, f.fd);
```

---

## Q7: Managers with 5+ Direct Reports

**Tables**: Employee (id, name, managerId) | **Key**: GROUP BY + HAVING

```sql
SELECT name FROM Employee WHERE id IN (
    SELECT managerId FROM Employee GROUP BY managerId HAVING COUNT(*) >= 5
);
```

---

## Q8: Investments in 2016

**Tables**: Insurance (pid, tiv_2015, tiv_2016, lat, lon) | **Key**: Duplicate/unique detection

```sql
WITH Dup AS (SELECT tiv_2015 FROM Insurance GROUP BY tiv_2015 HAVING COUNT(*) > 1),
Uniq AS (SELECT lat, lon FROM Insurance GROUP BY lat, lon HAVING COUNT(*) = 1)
SELECT ROUND(SUM(i.tiv_2016), 2) tiv_2016 FROM Insurance i
JOIN Dup d ON i.tiv_2015 = d.tiv_2015 JOIN Uniq u ON i.lat = u.lat AND i.lon = u.lon;
```

---

## Q9: Friend Requests II (Most Friends)

**Tables**: RequestAccepted (requester_id, accepter_id) | **Key**: UNION ALL both sides

```sql
WITH All AS (SELECT requester_id id FROM RequestAccepted UNION ALL SELECT accepter_id FROM RequestAccepted)
SELECT TOP 1 id, COUNT(*) num FROM All GROUP BY id ORDER BY num DESC;
```

---

## Q10: Tree Node

**Tables**: Tree (id, p_id) | **Key**: CASE WHEN for Root/Inner/Leaf

```sql
SELECT id, CASE 
    WHEN p_id IS NULL THEN 'Root'
    WHEN id IN (SELECT p_id FROM Tree WHERE p_id IS NOT NULL) THEN 'Inner'
    ELSE 'Leaf' END AS type
FROM Tree;
```

---

## Q11: Exchange Seats

**Tables**: Seat (id, student) | **Key**: Modulo for odd/even swap

```sql
SELECT CASE 
    WHEN id % 2 = 1 AND id = (SELECT COUNT(*) FROM Seat) THEN id
    WHEN id % 2 = 1 THEN id + 1 ELSE id - 1 END AS id, student
FROM Seat ORDER BY id;
```

---

## Q12: Customers Who Bought All Products

**Tables**: Customer, Product | **Key**: COUNT DISTINCT = total products

```sql
SELECT customer_id FROM Customer GROUP BY customer_id
HAVING COUNT(DISTINCT product_key) = (SELECT COUNT(*) FROM Product);
```

---

## Q13: Product Sales Analysis III

**Tables**: Sales (product_id, year, quantity, price) | **Key**: MIN year per product

```sql
WITH First AS (SELECT product_id, MIN(year) first_year FROM Sales GROUP BY product_id)
SELECT s.product_id, f.first_year, s.quantity, s.price FROM Sales s
JOIN First f ON s.product_id = f.product_id AND s.year = f.first_year;
```

---

## Q14: Market Analysis I

**Tables**: Users, Orders | **Key**: LEFT JOIN + conditional SUM

```sql
SELECT u.user_id buyer_id, u.join_date, 
    SUM(CASE WHEN YEAR(o.order_date) = 2019 THEN 1 ELSE 0 END) orders_in_2019
FROM Users u LEFT JOIN Orders o ON u.user_id = o.buyer_id GROUP BY u.user_id, u.join_date;
```

---

## Q15: Product Price at a Given Date

**Tables**: Products (product_id, new_price, change_date) | **Key**: Latest before date

```sql
WITH Latest AS (
    SELECT product_id, new_price, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY change_date DESC) rn
    FROM Products WHERE change_date <= '2019-08-16'
)
SELECT product_id, new_price price FROM Latest WHERE rn = 1
UNION
SELECT DISTINCT product_id, 10 FROM Products WHERE product_id NOT IN 
    (SELECT product_id FROM Products WHERE change_date <= '2019-08-16');
```

---

## Q16: Immediate Food Delivery II

**Tables**: Delivery | **Key**: First order + immediate %

```sql
WITH First AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) rn FROM Delivery)
SELECT ROUND(100.0 * SUM(CASE WHEN order_date = customer_pref_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) immediate_percentage
FROM First WHERE rn = 1;
```

---

## Q17: Monthly Transactions I

**Tables**: Transactions | **Key**: FORMAT + conditional aggregation

```sql
SELECT FORMAT(trans_date, 'yyyy-MM') month, country, COUNT(*) trans_count,
    SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END) approved_count,
    SUM(amount) trans_total_amount,
    SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END) approved_total_amount
FROM Transactions GROUP BY FORMAT(trans_date, 'yyyy-MM'), country;
```

---

## Q18: Last Person to Fit in the Bus

**Tables**: Queue (person_name, weight, turn) | **Key**: Running SUM

```sql
WITH CTE AS (SELECT person_name, turn, SUM(weight) OVER (ORDER BY turn) total FROM Queue)
SELECT TOP 1 person_name FROM CTE WHERE total <= 1000 ORDER BY turn DESC;
```

---

## Q19: Restaurant Growth

**Tables**: Customer (visited_on, amount) | **Key**: 7-day moving average

```sql
WITH Daily AS (SELECT visited_on, SUM(amount) amt FROM Customer GROUP BY visited_on),
Moving AS (SELECT visited_on, SUM(amt) OVER (ORDER BY visited_on ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) amount,
    AVG(1.0*amt) OVER (ORDER BY visited_on ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) avg_amt,
    ROW_NUMBER() OVER (ORDER BY visited_on) rn FROM Daily)
SELECT visited_on, amount, ROUND(avg_amt, 2) average_amount FROM Moving WHERE rn >= 7;
```
