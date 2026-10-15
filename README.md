# Workforce Attrition & Retention Analytics

**👉 Case study: https://your-username.github.io/workforce-attrition-analytics/**

A business-analysis case study for **NimbusTech**, a fictional 1,200-person software company.
Attrition in its product teams (Engineering, Product, Data) jumped from 14% to **22%** in one year,
adding **$1.8M** in replacement hiring costs.

## The short version

| | |
|---|---|
| **Problem** | Product-team attrition hit 21.7% in 2025 (rest of company: 14%) |
| **Main causes** | Overtime above 20 hrs/month (2× risk), two struggling managers (half of Engineering exits), no promotion in 2+ years (3× risk), senior staff paid below market (4× risk), first-year exits |
| **Ruled out** | Commute, remote vs office, gender |
| **Recommendation** | Six targeted actions, starting with stay interviews for 43 high-risk employees |
| **Business case** | Returning to 14% saves about **$1.66M a year** |

## Tools

- **Excel**: data cleaning (Power Query), data-quality log, savings model
- **SQL**: answering the business questions (`/sql`, one file per question)
- **Power BI**: monitoring dashboard for HR (`/powerbi`)

## What's in this repo

| Folder | Contents |
|---|---|
| `index.html`, `assets/` | The case-study page |
| `data/` | Raw and clean data, data dictionary, assumptions, SQLite database |
| `sql/` | The analysis queries; each file starts with the business question it answers |
| `excel/` | Cleaning workbook and savings model |
| `powerbi/` | Dashboard file |
| `images/` | Dashboard screenshots used on the page |
| `behind-the-scenes/` | Script that generated the synthetic dataset |

## About the data

The company and data are fictional and synthetic, built to reflect common tech-industry attrition
patterns. See [`data/assumptions.md`](data/assumptions.md) for how it was built.

---
Built by **[Your Name]** · [LinkedIn](https://www.linkedin.com/in/your-profile) · [Email](mailto:you@example.com)
