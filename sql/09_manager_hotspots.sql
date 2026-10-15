-- Business question: Are some teams losing people because of their manager?
-- Engineering managers ranked by the share of their 2025 team who left.

SELECT m.ManagerName,
       p.ManagerID,
       m.ManagerTenureYears,
       COUNT(*) AS TeamSize2025,
       SUM(p.LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(p.LeftIn2025) / COUNT(*), 1) AS PctLeft,
       ROUND(AVG(p.JobSatisfaction), 1) AS AvgJobSatisfaction
FROM product_teams_2025 p
JOIN managers m ON p.ManagerID = m.ManagerID
WHERE p.Department = 'Engineering'
GROUP BY m.ManagerName, p.ManagerID, m.ManagerTenureYears
ORDER BY PctLeft DESC;
