# Data dictionary

Fictional company: **NimbusTech** · Period: 1 Jan 2023 – 31 Dec 2025 · Analysis date: **31 Dec 2025**

| File | Rows | What it is |
|---|---|---|
| `raw/employees_raw.csv` | 1,647 | HR export **before** cleaning (contains planted data issues) |
| `clean/employees_clean.csv` | 1,632 | One row per person employed at any time in 2023–2025 |
| `clean/departments.csv` | 8 | Department lookup: critical-team flag and cost assumptions |
| `clean/managers.csv` | 60 | People managers |
| `nimbustech.db` | — | SQLite database with all of the above plus ready-made views |

## employees

| Column | Description | Example |
|---|---|---|
| EmployeeID | Unique ID | EMP10418 |
| Department | One of 8 departments (join to `departments`) | Engineering |
| Team | Team within the department | Payments |
| JobRole | Job title (level prefix + job family) | Senior Software Engineer |
| JobLevel | L1 (entry) to L5 (principal) | L3 |
| ManagerID | Join to `managers` | MGR-ENG-03 |
| HireDate | Date joined | 2023-04-17 |
| TerminationDate | Date left; blank if still employed | 2025-06-09 |
| Attrition | Yes = has left, No = still employed | Yes |
| ExitType | Voluntary or Involuntary; blank if still employed | Voluntary |
| ExitReason | Main reason from the exit interview | Burnout & Workload |
| Age | Age on the termination date or the analysis date | 34 |
| Gender | Male / Female / Non-binary | Female |
| Education | Associate / Bachelor's / Master's / Doctorate | Master's |
| WorkMode | Remote / Hybrid / Onsite | Hybrid |
| CommuteMiles | One-way commute; 0 for remote | 14 |
| AnnualSalaryUSD | Salary at exit or analysis date | 131200 |
| MarketMedianSalaryUSD | Market median salary for the same role and level | 152500 |
| MonthlyOvertimeHours | Average overtime hours per month (latest) | 22 |
| JobSatisfaction | Survey score, 1 (low) – 5 (high) | 2 |
| WorkLifeBalance | Survey score, 1 (low) – 5 (high) | 2 |
| EngagementScore | Engagement index, 0 – 100 | 58 |
| PerformanceRating | Latest rating, 1 (low) – 5 (high) | 4 |
| PromotionsLast3Years | Promotions in the 3 years before exit or analysis date | 0 |
| MonthsSinceLastPromotion | Months since last promotion (or since hire if never promoted) | 31 |
| TrainingHoursLastYear | Training hours completed in the last year | 24 |
| DataQualityFlag | *Clean file only.* What was fixed in this row, if anything | Salary imputed (role median) |

## departments

| Column | Description |
|---|---|
| Department | Department name |
| IsCriticalProductTeam | Yes for Engineering, Product, Data |
| ReplacementCostMultiplier | Share of salary it costs to replace a leaver (0.5 = 50%) |
| AvgTimeToFillDays | Typical days to fill an open role |

## managers

| Column | Description |
|---|---|
| ManagerID | Unique manager ID |
| ManagerName | Fictional name |
| Department | Department managed |
| ManagerTenureYears | Years as a people manager |
| SpanOfControl | Current direct reports (as of analysis date) |

## Ready-made views in `nimbustech.db`

| View | What it is |
|---|---|
| `staff` | Employees with their department details attached |
| `product_teams_2025` | Product-team employees who worked any time in 2025, plus `LeftIn2025` (1/0), `TenureYears` and `PayVsMarket` (salary ÷ market median) |

## Key definitions

- **Annual attrition rate** = leavers during the year ÷ average headcount, where average headcount = (headcount on 1 Jan + headcount on 31 Dec) ÷ 2.
- **% who left (driver analysis)** = share of a group employed during 2025 who left during 2025.
- **Replacement cost** = annual salary × department multiplier.
- **Pay vs market** = salary ÷ market median; below 0.90 means paid 10% or more under market.
