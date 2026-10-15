-- Business question: When in their journey do people leave?

-- Share of 2025 employees who left, by tenure band
SELECT CASE
           WHEN TenureYears < 1 THEN '1. Under 1 year'
           WHEN TenureYears < 2 THEN '2. 1-2 years'
           WHEN TenureYears < 4 THEN '3. 2-4 years'
           ELSE '4. 4+ years'
       END AS TenureBand,
       COUNT(*) AS Employees,
       SUM(LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
GROUP BY TenureBand
ORDER BY TenureBand;

-- What share of all 2025 leavers left within their first year?
SELECT ROUND(100.0 * SUM(CASE WHEN TenureYears < 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS PctOfLeaversInFirstYear
FROM product_teams_2025
WHERE LeftIn2025 = 1;
