-- =========================================================
-- ADVANCED SQL CHALLENGES
-- =========================================================

-- ---------------------------------------------------------
-- QUESTION 6: Recursive CTE (Hierarchy)
-- "Given an Employee table (id, name, manager_id), find the hierarchy path for a specific employee."
-- ---------------------------------------------------------

WITH RECURSIVE EmployeeHierarchy AS (
    -- Anchor member: Start with the specific employee (e.g., ID 5)
    SELECT id, name, manager_id, CAST(name AS CHAR(200)) as path, 1 as level
    FROM Employees
    WHERE id = 5
    
    UNION ALL
    
    -- Recursive member: Join with manager
    SELECT e.id, e.name, e.manager_id, CONCAT(eh.path, ' -> ', e.name), eh.level + 1
    FROM Employees e
    INNER JOIN EmployeeHierarchy eh ON e.id = eh.manager_id
)
SELECT * FROM EmployeeHierarchy;

-- ---------------------------------------------------------
-- QUESTION 7: Pivot (Rows to Columns)
-- "Transform monthly sales data into columns for each month."
-- Source: Sales (product, month, amount)
-- Target: Product, Jan_Sales, Feb_Sales, ...
-- ---------------------------------------------------------

SELECT 
    product,
    SUM(CASE WHEN month = 'Jan' THEN amount ELSE 0 END) as Jan_Sales,
    SUM(CASE WHEN month = 'Feb' THEN amount ELSE 0 END) as Feb_Sales,
    SUM(CASE WHEN month = 'Mar' THEN amount ELSE 0 END) as Mar_Sales
FROM Sales
GROUP BY product;

-- ---------------------------------------------------------
-- QUESTION 8: Sessionization (Gaps and Islands)
-- "Group user events into sessions. A new session starts if there is a gap of > 30 mins."
-- ---------------------------------------------------------

WITH LaggedEvents AS (
    SELECT 
        user_id, 
        event_time,
        LAG(event_time) OVER(PARTITION BY user_id ORDER BY event_time) as prev_event_time
    FROM UserEvents
),
NewSessionFlags AS (
    SELECT 
        user_id,
        event_time,
        CASE 
            WHEN prev_event_time IS NULL THEN 1
            WHEN TIMESTAMPDIFF(MINUTE, prev_event_time, event_time) > 30 THEN 1
            ELSE 0
        END as is_new_session
    FROM LaggedEvents
),
SessionGroups AS (
    SELECT 
        user_id,
        event_time,
        SUM(is_new_session) OVER(PARTITION BY user_id ORDER BY event_time) as session_id
    FROM NewSessionFlags
)
SELECT 
    user_id, 
    session_id, 
    MIN(event_time) as session_start, 
    MAX(event_time) as session_end,
    COUNT(*) as events_in_session
FROM SessionGroups
GROUP BY user_id, session_id;

-- ---------------------------------------------------------
-- QUESTION 9: Deduplication with Logic
-- "Keep only the most recent record. If there's a tie in date, keep the one with highest ID."
-- ---------------------------------------------------------

DELETE FROM Claims
WHERE claim_id IN (
    SELECT claim_id FROM (
        SELECT 
            claim_id,
            ROW_NUMBER() OVER(
                PARTITION BY policy_no 
                ORDER BY claim_date DESC, claim_id DESC
            ) as rn
        FROM Claims
    ) t
    WHERE rn > 1
);
