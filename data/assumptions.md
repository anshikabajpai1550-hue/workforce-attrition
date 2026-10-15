# Assumptions and how the data was built

NimbusTech is **fictional** and the data is **synthetic**. It was generated to support a realistic
business-analysis case study, using patterns widely reported in tech-industry attrition research.
Nothing here describes a real company or real people.

## Business scenario

- Mid-sized software company, about 970 employees in Jan 2023 growing to 1,176 by Dec 2025.
- "Critical product teams" = Engineering, Product and Data (about 340 people in 2025).
- Product-team attrition: **11.9% (2023) → 14.0% (2024) → 21.7% (2025)**. Rest of company: 13–14% each year.
- Product-team replacement cost: $2.27M → $2.90M → $4.68M, an increase of **$1.77M** in 2025.

## Cost assumptions

| Department group | Replacement cost (% of salary) | Why |
|---|---|---|
| Engineering, Product, Data | 50% | Low end of the commonly cited 50–200% range for skilled technical roles |
| Sales, Marketing, Finance, HR | 30% | Mid-skill professional roles |
| Customer Support | 20% | Faster, lower-cost hiring |

## How the data was generated

The company was simulated month by month for 36 months. Each month, some people were hired,
promoted, or left. The number of leavers per group was set to match the target attrition rates.
**Who** left was decided by these built-in risk factors:

| Factor | Effect on chance of leaving |
|---|---|
| Overtime above 20 hrs/month | About 3× higher. Product teams worked more overtime in 2025 (release crunch) |
| No promotion in 24+ months | About 2× higher. Promotions in product teams slowed in 2024–25 |
| Paid 10%+ below market, senior levels (L3–L5) | About 2× higher. Little effect for junior levels |
| First 12 months at the company | About 3× higher |
| Two specific Engineering managers (both new to managing) | About 2.6× higher |
| Top performers in product teams | Slightly higher (they have more outside options) |
| 40+ training hours a year | Slightly lower |
| Gender, commute distance, work mode, education, age | **No effect** (by design) |

Survey scores (satisfaction, work-life balance, engagement) were generated to be consistent with
these factors: for example, more overtime leads to lower work-life balance.

The generator was run with a fixed random seed and checked automatically: it only accepts a dataset
where the headline numbers match the scenario, the designed patterns are visible, and factors with
no effect don't show a gap by chance.

## Planted data-quality issues (raw file only)

| Issue | Count | How it was fixed in the clean file |
|---|---|---|
| Duplicate rows (double export) | 15 | Removed |
| Missing salary | 20 | Filled with the median salary for the same job role; flagged |
| Inconsistent department names (case, spaces, "HR") | 25 | Standardized to the 8 official names |
| Extra spaces in job titles | 30 | Trimmed |
| Hire and termination dates swapped | 8 | Swapped back; flagged |
| Employee IDs typed as "emp-12345" | 3 | Reformatted to "EMP12345" |

## Limitations

- Synthetic data shows how the analysis works. It doesn't replace validation with real HR data.
- The analysis shows associations, not proven causes. In practice, I'd confirm the findings with
  exit-interview themes and pilot the interventions before rolling them out.
- Replacement cost leaves out productivity lost while a role is open, so savings are understated.
