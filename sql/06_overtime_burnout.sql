-- Business question: Is overwork driving people out?

SELECT CASE
           WHEN MonthlyOvertimeHours <= 10 THEN '1. 0-10 hrs'
           WHEN MonthlyOvertimeHours <= 20 THEN '2. 11-20 hrs'
           ELSE '3. Over 20 hrs'
       END AS OvertimeBand,
       COUNT(*) AS Employees,
       SUM(LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft,
       ROUND(AVG(WorkLifeBalance), 1) AS AvgWorkLifeBalance
FROM product_teams_2025
GROUP BY OvertimeBand
ORDER BY OvertimeBand;
