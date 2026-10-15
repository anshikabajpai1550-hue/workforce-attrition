-- Business question: Is pay the problem, and for whom?
-- PayVsMarket = salary / market median for the same role and level (1.00 = paid at market).

SELECT CASE WHEN JobLevel IN ('L3', 'L4', 'L5') THEN 'Senior (L3-L5)' ELSE 'Junior (L1-L2)' END AS Seniority,
       CASE WHEN PayVsMarket < 0.90 THEN 'Paid 10%+ below market' ELSE 'Paid at/near market' END AS PayPosition,
       COUNT(*) AS Employees,
       SUM(LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft
FROM product_teams_2025
GROUP BY Seniority, PayPosition
ORDER BY Seniority DESC, PayPosition;
