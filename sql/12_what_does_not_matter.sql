-- Business question: Which popular explanations are NOT supported by the data?
-- Ruling things out saves money on the wrong fixes.

-- Commute distance (office-based and hybrid staff only)
SELECT CASE WHEN CommuteMiles > 20 THEN 'Over 20 miles' ELSE '20 miles or less' END AS Commute,
       COUNT(*) AS Employees,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
WHERE WorkMode <> 'Remote'
GROUP BY Commute;

-- Work mode
SELECT WorkMode,
       COUNT(*) AS Employees,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
GROUP BY WorkMode;

-- Fairness check: leaving rate by gender
SELECT Gender,
       COUNT(*) AS Employees,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
GROUP BY Gender;
