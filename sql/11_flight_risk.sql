-- Business question: Which current product-team employees are most at risk of leaving?
-- A simple points score built from the drivers found in files 05-09. Not a prediction model.

WITH scored AS (
    SELECT EmployeeID, Department, Team, JobRole, ManagerID, PerformanceRating,
           (CASE WHEN MonthlyOvertimeHours > 20 THEN 2 ELSE 0 END
          + CASE WHEN MonthsSinceLastPromotion > 24 THEN 2 ELSE 0 END
          + CASE WHEN PayVsMarket < 0.90 AND JobLevel IN ('L3', 'L4', 'L5') THEN 2 ELSE 0 END
          + CASE WHEN ManagerID IN ('MGR-ENG-03', 'MGR-ENG-08') THEN 2 ELSE 0 END
          + CASE WHEN TenureYears < 1 THEN 1 ELSE 0 END
          + CASE WHEN WorkLifeBalance <= 2 THEN 1 ELSE 0 END) AS RiskScore
    FROM product_teams_2025
    WHERE TerminationDate IS NULL
)
SELECT CASE WHEN RiskScore >= 5 THEN '1. High'
            WHEN RiskScore >= 3 THEN '2. Medium'
            ELSE '3. Low' END AS RiskLevel,
       COUNT(*) AS Employees,
       SUM(CASE WHEN PerformanceRating >= 4 THEN 1 ELSE 0 END) AS HighPerformers
FROM scored
GROUP BY RiskLevel
ORDER BY RiskLevel;

-- The named list HR business partners would use for stay interviews:
-- re-run the CTE above and replace the final SELECT with
--   SELECT * FROM scored WHERE RiskScore >= 5 ORDER BY RiskScore DESC, PerformanceRating DESC;
