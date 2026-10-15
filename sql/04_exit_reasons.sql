-- Business question: Why are product-team employees leaving?
-- Exit reasons for everyone who left a product team in 2025.

SELECT ExitReason,
       ExitType,
       COUNT(*) AS Leavers,
       ROUND(100.0 * COUNT(*) / (SELECT SUM(LeftIn2025) FROM product_teams_2025), 1) AS PctOfLeavers
FROM product_teams_2025
WHERE LeftIn2025 = 1
GROUP BY ExitReason, ExitType
ORDER BY Leavers DESC;
