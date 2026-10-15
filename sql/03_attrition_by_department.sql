-- Business question: Which departments and teams are losing the most people in 2025?

-- By department (same formula as the headline rate)
SELECT Department,
       IsCriticalProductTeam,
       SUM(CASE WHEN HireDate <= '2025-01-01' AND (TerminationDate IS NULL OR TerminationDate > '2025-01-01') THEN 1 ELSE 0 END) AS HeadcountStart,
       SUM(CASE WHEN TerminationDate IS NULL THEN 1 ELSE 0 END) AS HeadcountEnd,
       SUM(CASE WHEN TerminationDate LIKE '2025%' THEN 1 ELSE 0 END) AS Leavers2025,
       ROUND(100.0 * SUM(CASE WHEN TerminationDate LIKE '2025%' THEN 1 ELSE 0 END)
             / ((SUM(CASE WHEN HireDate <= '2025-01-01' AND (TerminationDate IS NULL OR TerminationDate > '2025-01-01') THEN 1 ELSE 0 END)
                 + SUM(CASE WHEN TerminationDate IS NULL THEN 1 ELSE 0 END)) / 2.0), 1) AS AttritionPct
FROM staff
GROUP BY Department, IsCriticalProductTeam
ORDER BY AttritionPct DESC;

-- By team inside the product teams: share of 2025 employees who left
SELECT Department,
       Team,
       COUNT(*) AS Employees2025,
       SUM(LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
GROUP BY Department, Team
ORDER BY PctLeft DESC;
