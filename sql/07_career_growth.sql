-- Business question: Do stalled careers push people out?
-- Only people with 2+ years of tenure, so everyone had a fair chance to be promoted.

SELECT CASE WHEN MonthsSinceLastPromotion > 24 THEN 'No promotion in 2+ years'
            ELSE 'Promoted in last 2 years' END AS PromotionStatus,
       COUNT(*) AS Employees,
       SUM(LeftIn2025) AS Leavers,
       ROUND(100.0 * SUM(LeftIn2025) / COUNT(*), 1) AS PctLeft,
       ROUND(AVG(JobSatisfaction), 1) AS AvgJobSatisfaction
FROM product_teams_2025
WHERE TenureYears >= 2
GROUP BY PromotionStatus;
