-- Run this once after opening data/nimbustech.db.
-- It creates two reusable "saved queries" (views) that the other files build on.

-- 1. Every employee, with their department's details attached
DROP VIEW IF EXISTS staff;
CREATE VIEW staff AS
SELECT e.*,
       d.IsCriticalProductTeam,
       d.ReplacementCostMultiplier
FROM employees e
JOIN departments d ON e.Department = d.Department;

-- 2. Critical product-team employees who worked at NimbusTech at any point in 2025,
--    with a simple 1/0 flag for whether they left during 2025
DROP VIEW IF EXISTS product_teams_2025;
CREATE VIEW product_teams_2025 AS
SELECT *,
       CASE WHEN TerminationDate BETWEEN '2025-01-01' AND '2025-12-31' THEN 1 ELSE 0 END AS LeftIn2025,
       ROUND((julianday(COALESCE(TerminationDate, '2025-12-31')) - julianday(HireDate)) / 365.25, 1) AS TenureYears,
       ROUND(1.0 * AnnualSalaryUSD / MarketMedianSalaryUSD, 2) AS PayVsMarket
FROM staff
WHERE IsCriticalProductTeam = 'Yes'
  AND HireDate <= '2025-12-31'
  AND (TerminationDate IS NULL OR TerminationDate >= '2025-01-01');
