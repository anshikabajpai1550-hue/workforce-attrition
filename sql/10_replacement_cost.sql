-- Business question: What is attrition costing us?
-- Replacement cost per leaver = annual salary x department multiplier
-- (0.5 for product teams: recruiting, onboarding and lost productivity).

SELECT strftime('%Y', TerminationDate) AS Year,
       COUNT(*) AS Leavers,
       ROUND(AVG(AnnualSalaryUSD)) AS AvgSalary,
       ROUND(SUM(AnnualSalaryUSD * ReplacementCostMultiplier)) AS ReplacementCostUSD
FROM staff
WHERE IsCriticalProductTeam = 'Yes'
  AND TerminationDate IS NOT NULL
GROUP BY Year
ORDER BY Year;

-- Cost of losing high performers (rating 4-5) in 2025
SELECT CASE WHEN PerformanceRating >= 4 THEN 'High performer' ELSE 'Other' END AS Performer,
       COUNT(*) AS Leavers,
       ROUND(SUM(AnnualSalaryUSD * ReplacementCostMultiplier)) AS ReplacementCostUSD
FROM product_teams_2025
WHERE LeftIn2025 = 1 AND ExitType = 'Voluntary'
GROUP BY Performer;
