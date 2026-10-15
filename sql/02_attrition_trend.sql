-- Business question: How big is the problem, and is it getting worse?
-- Annual attrition rate = people who left in the year / average headcount
-- (average of headcount on 1 Jan and 31 Dec), split by critical product teams vs the rest.

WITH years AS (
    SELECT 2023 AS Yr UNION ALL SELECT 2024 UNION ALL SELECT 2025
),
yearly AS (
    SELECT y.Yr,
           s.IsCriticalProductTeam,
           SUM(CASE WHEN s.HireDate <= y.Yr || '-01-01'
                     AND (s.TerminationDate IS NULL OR s.TerminationDate > y.Yr || '-01-01')
                    THEN 1 ELSE 0 END) AS HeadcountStart,
           SUM(CASE WHEN s.HireDate <= y.Yr || '-12-31'
                     AND (s.TerminationDate IS NULL OR s.TerminationDate > y.Yr || '-12-31')
                    THEN 1 ELSE 0 END) AS HeadcountEnd,
           SUM(CASE WHEN strftime('%Y', s.TerminationDate) = CAST(y.Yr AS TEXT)
                    THEN 1 ELSE 0 END) AS Leavers
    FROM years y
    CROSS JOIN staff s
    GROUP BY y.Yr, s.IsCriticalProductTeam
)
SELECT Yr AS Year,
       CASE WHEN IsCriticalProductTeam = 'Yes' THEN 'Product teams' ELSE 'Rest of company' END AS TeamGroup,
       HeadcountStart,
       HeadcountEnd,
       Leavers,
       ROUND(100.0 * Leavers / ((HeadcountStart + HeadcountEnd) / 2.0), 1) AS AttritionPct
FROM yearly
ORDER BY TeamGroup, Year;
