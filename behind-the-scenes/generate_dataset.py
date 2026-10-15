"""
Generates the synthetic NimbusTech workforce dataset (2023-01-01 to 2025-12-31).

The company is simulated month by month: employees are hired, promoted and leave
based on documented risk factors (see data/assumptions.md). A fixed seed makes
the output identical on every run.

Usage:  python3 generate_dataset.py
Outputs: data/raw/*.csv, data/clean/*.csv, data/nimbustech.db
"""

import csv
import math
import random
import sqlite3
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MONTHS = 36  # Jan 2023 .. Dec 2025
ANALYSIS_DATE = date(2025, 12, 31)

DEPARTMENTS = {
    # name: (critical, start headcount, cost multiplier, days to fill, manager code)
    "Engineering":      (True, 215, 0.50, 62, "ENG"),
    "Product":          (True, 36, 0.50, 55, "PRD"),
    "Data":             (True, 34, 0.50, 58, "DAT"),
    "Sales":            (False, 250, 0.30, 38, "SAL"),
    "Customer Support": (False, 215, 0.20, 24, "SUP"),
    "Marketing":        (False, 105, 0.30, 40, "MKT"),
    "Finance":          (False, 62, 0.30, 45, "FIN"),
    "Human Resources":  (False, 48, 0.30, 42, "HR"),
}

# department -> list of (team, job family, weight)
TEAMS = {
    "Engineering": [("Core Platform", "Software Engineer", 3), ("Payments", "Software Engineer", 2),
                    ("Mobile Apps", "Software Engineer", 2), ("Web App", "Software Engineer", 2),
                    ("Infrastructure", "DevOps Engineer", 1.5), ("Quality", "QA Engineer", 1.5)],
    "Product": [("Product Management", "Product Manager", 3), ("Design", "Product Designer", 2)],
    "Data": [("Analytics", "Data Analyst", 2), ("Data Engineering", "Data Engineer", 1.5),
             ("Data Science", "Data Scientist", 1)],
    "Sales": [("SMB Sales", "Account Executive", 3), ("Mid-Market Sales", "Account Executive", 2),
              ("Enterprise Sales", "Account Executive", 1.5), ("Sales Development", "Sales Development Rep", 2.5)],
    "Customer Support": [("Tier 1 Support", "Support Specialist", 3), ("Tier 2 Support", "Support Specialist", 2),
                         ("Customer Onboarding", "Onboarding Specialist", 1)],
    "Marketing": [("Growth", "Growth Marketer", 2), ("Content", "Content Marketer", 1.5),
                  ("Product Marketing", "Product Marketer", 1)],
    "Finance": [("FP&A", "Financial Analyst", 2), ("Accounting", "Accountant", 2)],
    "Human Resources": [("People Operations", "HR Generalist", 2), ("Talent Acquisition", "Recruiter", 1.5)],
}

# Market median salary for a level-2 role in each job family (USD)
MARKET_BASE = {
    "Software Engineer": 122000, "DevOps Engineer": 126000, "QA Engineer": 102000,
    "Product Manager": 132000, "Product Designer": 112000, "Data Analyst": 92000,
    "Data Engineer": 126000, "Data Scientist": 132000, "Account Executive": 74000,
    "Sales Development Rep": 58000, "Support Specialist": 52000, "Onboarding Specialist": 58000,
    "Growth Marketer": 76000, "Content Marketer": 68000, "Product Marketer": 88000,
    "Financial Analyst": 82000, "Accountant": 72000, "HR Generalist": 68000, "Recruiter": 70000,
}
LEVEL_MULT = {1: 0.80, 2: 1.00, 3: 1.25, 4: 1.50, 5: 1.85}
LEVEL_PREFIX = {1: "Associate ", 2: "", 3: "Senior ", 4: "Lead ", 5: "Principal "}
LEVEL_AGE = {1: (22, 30), 2: (24, 38), 3: (28, 48), 4: (32, 55), 5: (36, 60)}

FIRST_NAMES = ["Aarav", "Maya", "Liam", "Sofia", "Noah", "Priya", "Ethan", "Zara", "Lucas", "Amara",
               "Owen", "Hana", "Mateo", "Chloe", "Ravi", "Elena", "Jonah", "Leila", "Samuel", "Nora",
               "Kenji", "Isla", "Daniel", "Freya", "Omar", "Grace", "Viktor", "Ana", "Felix", "Mei",
               "Arjun", "Ruth", "Diego", "Tessa", "Ivan", "Lena", "Marcus", "Yara", "Caleb", "Ines",
               "Hugo", "Asha", "Theo", "Nadia", "Rohan", "Clara", "Andre", "Simone", "Kofi", "Julia"]
LAST_NAMES = ["Shah", "Reyes", "Okafor", "Lindqvist", "Tanaka", "Moreau", "Kowalski", "Haddad", "Brennan",
              "Mehta", "Novak", "Silva", "Park", "Fischer", "Adeyemi", "Rossi", "Kaur", "Bauer", "Duarte",
              "Ivanova", "Nakamura", "Osei", "Larsen", "Gupta", "Weber", "Costa", "Murphy", "Ali", "Jensen",
              "Petrov", "Chen", "Dubois", "Mendes", "Kim", "Sato", "Hughes", "Varga", "Ortiz", "Nair", "Wolfe"]

GROWTH_PER_MONTH = 0.0055
# Annual attrition targets used to calibrate the base exit risk
TARGETS = {True: {2023: 0.12, 2024: 0.14, 2025: 0.22}, False: {2023: 0.13, 2024: 0.135, 2025: 0.14}}


def month_to_date(t, rng):
    year, month = 2023 + t // 12, t % 12 + 1
    return date(year, month, rng.randint(1, 28))


def year_of(t):
    return 2023 + t // 12


def weighted(rng, options):
    total = sum(w for _, w in options)
    r = rng.uniform(0, total)
    for value, w in options:
        r -= w
        if r <= 0:
            return value
    return options[-1][0]


class Sim:
    def __init__(self, seed, scales):
        self.rng = random.Random(seed)
        self.scales = scales
        self.people = []
        self.managers = {}
        self.next_id = 10001
        self._build_managers()

    def _build_managers(self):
        rng = self.rng
        used = set()
        for dept, (crit, start, _, _, code) in DEPARTMENTS.items():
            n = max(3, round(start / 17))
            ids = []
            for i in range(1, n + 1):
                while True:
                    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
                    if name not in used:
                        used.add(name)
                        break
                mid = f"MGR-{code}-{i:02d}"
                self.managers[mid] = {"ManagerID": mid, "ManagerName": name, "Department": dept,
                                      "ManagerTenureYears": round(rng.uniform(1.0, 9.0), 1), "hotspot": False}
                ids.append(mid)
            if dept == "Engineering":
                # Two managers whose teams churn far more than everyone else's
                for mid in ("MGR-ENG-03", "MGR-ENG-08"):
                    self.managers[mid]["hotspot"] = True
                    self.managers[mid]["ManagerTenureYears"] = round(rng.uniform(0.8, 1.6), 1)
            DEPARTMENTS_MANAGERS.setdefault(dept, ids)

    def new_person(self, dept, hire_t, initial):
        rng = self.rng
        crit = DEPARTMENTS[dept][0]
        team, family = weighted(rng, [((t, f), w) for t, f, w in TEAMS[dept]])
        if initial:
            level = weighted(rng, [(1, 18), (2, 34), (3, 30), (4, 13), (5, 5)])
        else:
            level = weighted(rng, [(1, 34), (2, 40), (3, 20), (4, 6)])
        if crit and level >= 3 and initial and rng.random() < 0.38:
            compa = rng.gauss(0.86, 0.035)  # tenured seniors who fell behind the market
        elif not initial:
            compa = rng.gauss(1.02, 0.05)   # new hires are hired at today's market rate
        else:
            compa = rng.gauss(1.0, 0.065)
        compa = min(max(compa, 0.75), 1.25)
        lo, hi = LEVEL_AGE[level]
        mgr = rng.choice(DEPARTMENTS_MANAGERS[dept])
        if dept == "Engineering" and self.managers[mgr]["hotspot"] is False and rng.random() < 0.06:
            mgr = rng.choice(["MGR-ENG-03", "MGR-ENG-08"])
        work_mode = weighted(rng, [("Remote", 35), ("Hybrid", 50), ("Onsite", 15)] if crit
                             else [("Remote", 20), ("Hybrid", 50), ("Onsite", 30)])
        if work_mode == "Remote":
            commute = 0
        else:
            commute = int(min(55, max(1, rng.lognormvariate(2.4, 0.7))))
        if hire_t < 0:
            tenure = -hire_t
            last_promo = None
            if tenure >= 12 and rng.random() < 0.75:
                last_promo = hire_t + rng.randint(12, max(12, tenure))
                last_promo = min(last_promo, -1)
            promos = [last_promo] if last_promo is not None else []
        else:
            promos = []
        p = {
            "id": None, "dept": dept, "crit": crit, "team": team, "family": family, "level": level,
            "compa": compa, "mgr": mgr, "hire_t": hire_t, "term_t": None, "exit_type": None,
            "exit_reason": None,
            "age_at_hire": rng.randint(lo, hi) - (max(0, -hire_t) // 12 if hire_t < 0 else 0),
            "gender": weighted(rng, [("Male", 52), ("Female", 44), ("Non-binary", 4)]),
            "education": weighted(rng, [("Bachelor's", 60), ("Master's", 28), ("Associate", 7),
                                        ("Doctorate", 5 if family != "Data Scientist" else 25)]),
            "work_mode": work_mode, "commute": commute,
            "overtime_base": min(40, max(0, rng.gauss(12, 5) if crit else rng.gauss(10, 5))),
            "performance": weighted(rng, [(1, 4), (2, 10), (3, 46), (4, 30), (5, 10)]),
            "training": rng.randint(0, 60), "promos": promos,
        }
        p["age_at_hire"] = max(21, p["age_at_hire"])
        return p

    def overtime(self, p, t):
        ot = p["overtime_base"]
        if p["crit"] and year_of(t) == 2025:
            ot += 6  # 2025 release crunch in product teams
        return min(40, ot)

    def months_since_promo(self, p, t):
        last = p["promos"][-1] if p["promos"] else p["hire_t"]
        return t - last

    def exit_risk(self, p, t):
        base = self.scales[p["crit"]][year_of(t)]
        m = 1.0
        ot = self.overtime(p, t)
        m *= 3.0 if ot > 20 else (1.3 if ot > 15 else 1.0)
        m *= 2.0 if self.months_since_promo(p, t) > 24 else 1.0
        if p["compa"] < 0.90:
            m *= 1.9 if p["level"] >= 3 else 1.1
        m *= 3.0 if (t - p["hire_t"]) <= 12 else 1.0
        m *= 2.6 if self.managers[p["mgr"]]["hotspot"] else 1.0
        m *= 1.25 if (p["crit"] and p["performance"] >= 4) else 1.0
        m *= 0.85 if p["training"] > 40 else 1.0
        return min(0.5, base * m)

    def pick_reason(self, p, t):
        rng = self.rng
        ot = self.overtime(p, t)
        options = [
            ("Burnout & Workload", 3.0 if ot > 20 else 0.4),
            ("Lack of Career Growth", 3.0 if self.months_since_promo(p, t) > 24 else 0.4),
            ("Below-Market Pay", 3.0 if (p["compa"] < 0.9 and p["level"] >= 3) else (1.0 if p["compa"] < 0.9 else 0.3)),
            ("Manager Relationship", 3.5 if self.managers[p["mgr"]]["hotspot"] else 0.3),
            ("Role Not as Expected", 2.0 if (t - p["hire_t"]) <= 12 else 0.1),
            ("Better Opportunity Elsewhere", 0.8),
            ("Relocation / Personal", 0.6),
        ]
        return weighted(rng, options)

    def run(self):
        rng = self.rng
        active = {d: [] for d in DEPARTMENTS}
        for dept, (_, start, *_rest) in DEPARTMENTS.items():
            for _ in range(start):
                tenure = int(min(120, 1 + rng.expovariate(1 / 40)))
                p = self.new_person(dept, -tenure, initial=True)
                self.people.append(p)
                active[dept].append(p)
        owed = {True: 0.0, False: 0.0}
        for t in range(MONTHS):
            for crit in (True, False):
                group = [p for d in DEPARTMENTS if DEPARTMENTS[d][0] == crit for p in active[d]]
                exits = 0
                for p in group:
                    if t > p["hire_t"] and rng.random() < (0.004 if p["performance"] <= 2 else 0.0004):
                        p["term_t"], p["exit_type"] = t, "Involuntary"
                        p["exit_reason"] = weighted(rng, [("Performance", 0.8), ("Restructuring", 0.2)])
                        exits += 1
                # Exit quota keeps the annual rate on target; risk factors decide who leaves
                owed[crit] += TARGETS[crit][year_of(t)] / 12 * len(group) - exits
                n = max(0, int(owed[crit]))
                owed[crit] -= n
                eligible = [p for p in group if p["term_t"] is None and t > p["hire_t"]]
                keyed = sorted(eligible, key=lambda p: rng.random() ** (1 / self.exit_risk(p, t)), reverse=True)
                for p in keyed[:n]:
                    p["term_t"], p["exit_type"] = t, "Voluntary"
                    p["exit_reason"] = self.pick_reason(p, t)
            for dept, (crit, start, *_rest) in DEPARTMENTS.items():
                still = []
                for p in active[dept]:
                    if p["term_t"] is not None:
                        continue
                    promo_rate = 0.025 if not crit else {2023: 0.025, 2024: 0.014, 2025: 0.009}[year_of(t)]
                    if self.months_since_promo(p, t) >= 12 and p["level"] < 5 and rng.random() < promo_rate:
                        p["level"] += 1
                        p["promos"].append(t)
                    still.append(p)
                target = round(start * (1 + GROWTH_PER_MONTH) ** (t + 1))
                for _ in range(max(0, target - len(still))):
                    p = self.new_person(dept, t, initial=False)
                    self.people.append(p)
                    still.append(p)
                active[dept] = still
        return self


DEPARTMENTS_MANAGERS = {}


def headcount_on(rows, d):
    return sum(1 for r in rows if r["HireDate"] <= d and (r["TerminationDate"] is None or r["TerminationDate"] > d))


def attrition_rates(rows, crit_flag):
    out = {}
    group = [r for r in rows if DEPARTMENTS[r["Department"]][0] == crit_flag]
    for y in (2023, 2024, 2025):
        start = headcount_on(group, date(y, 1, 1).isoformat())
        end = headcount_on(group, date(y, 12, 31).isoformat())
        leavers = sum(1 for r in group if r["TerminationDate"] and r["TerminationDate"][:4] == str(y))
        out[y] = {"leavers": leavers, "avg_hc": (start + end) / 2, "rate": leavers / ((start + end) / 2)}
    return out


def replacement_cost(rows, year):
    return sum(r["AnnualSalaryUSD"] * DEPARTMENTS[r["Department"]][2] for r in rows
               if DEPARTMENTS[r["Department"]][0] and r["TerminationDate"]
               and r["TerminationDate"][:4] == str(year))


def to_rows(sim):
    rng = random.Random(7)
    people = sorted(sim.people, key=lambda p: (p["hire_t"], p["dept"]))
    rows = []
    for i, p in enumerate(people):
        p["id"] = f"EMP{10001 + i}"
        hire = month_to_date(p["hire_t"], rng)
        term = month_to_date(p["term_t"], rng) if p["term_t"] is not None else None
        if term and term <= hire:
            term = date(term.year, term.month, 28)
        end_t = p["term_t"] if p["term_t"] is not None else MONTHS - 1
        end_date = term or ANALYSIS_DATE
        market = MARKET_BASE[p["family"]] * LEVEL_MULT[p["level"]]
        salary = round(market * p["compa"] / 100) * 100
        ot = sim.overtime(p, end_t) if p["term_t"] is not None else sim.overtime(p, MONTHS - 1)
        ot = round(ot + rng.gauss(0, 1.5))
        ot = min(40, max(0, ot))
        msp = sim.months_since_promo(p, end_t)
        promos_3y = sum(1 for x in p["promos"] if end_t - 36 < x <= end_t)
        hotspot = sim.managers[p["mgr"]]["hotspot"]
        left = p["term_t"] is not None and p["exit_type"] == "Voluntary"
        wlb = 4.3 - (ot - 10) / 6 + rng.gauss(0, 0.6) - (0.4 if left else 0)
        sat = (3.8 - (0.8 if msp > 24 else 0) - (0.9 if hotspot else 0)
               - (0.5 if p["compa"] < 0.9 else 0) + rng.gauss(0, 0.7) - (0.6 if left else 0))
        wlb, sat = min(5, max(1, round(wlb))), min(5, max(1, round(sat)))
        engagement = min(100, max(5, round(30 + 8 * sat + 5 * wlb + rng.gauss(0, 6))))
        age = p["age_at_hire"] + (end_date - hire).days // 365
        rows.append({
            "EmployeeID": p["id"], "Department": p["dept"], "Team": p["team"],
            "JobRole": LEVEL_PREFIX[p["level"]] + p["family"], "JobLevel": f"L{p['level']}",
            "ManagerID": p["mgr"], "HireDate": hire.isoformat(),
            "TerminationDate": term.isoformat() if term else None,
            "Attrition": "Yes" if term else "No", "ExitType": p["exit_type"], "ExitReason": p["exit_reason"],
            "Age": age, "Gender": p["gender"], "Education": p["education"], "WorkMode": p["work_mode"],
            "CommuteMiles": p["commute"], "AnnualSalaryUSD": salary,
            "MarketMedianSalaryUSD": round(market / 100) * 100, "MonthlyOvertimeHours": ot,
            "JobSatisfaction": sat, "WorkLifeBalance": wlb, "EngagementScore": engagement,
            "PerformanceRating": p["performance"], "PromotionsLast3Years": promos_3y,
            "MonthsSinceLastPromotion": msp, "TrainingHoursLastYear": p["training"],
        })
    return rows


EMP_COLUMNS = ["EmployeeID", "Department", "Team", "JobRole", "JobLevel", "ManagerID", "HireDate",
               "TerminationDate", "Attrition", "ExitType", "ExitReason", "Age", "Gender", "Education",
               "WorkMode", "CommuteMiles", "AnnualSalaryUSD", "MarketMedianSalaryUSD", "MonthlyOvertimeHours",
               "JobSatisfaction", "WorkLifeBalance", "EngagementScore", "PerformanceRating",
               "PromotionsLast3Years", "MonthsSinceLastPromotion", "TrainingHoursLastYear"]


def make_raw(rows):
    """Plant a small, realistic set of data-entry issues."""
    rng = random.Random(99)
    raw = [dict(r) for r in rows]
    idx = list(range(len(raw)))
    rng.shuffle(idx)
    picks = iter(idx)
    for _ in range(20):  # missing salary
        raw[next(picks)]["AnnualSalaryUSD"] = None
    variants = ["engineering", "ENGINEERING", "Engineering ", "customer support", "Customer support",
                "sales", " Sales", "marketing", "Finance ", "human resources", "HR"]
    for _ in range(26):  # inconsistent department labels
        i = next(picks)
        options = [v for v in variants if v.strip().lower() == raw[i]["Department"].lower()
                   or (v == "HR" and raw[i]["Department"] == "Human Resources")]
        if options:
            raw[i]["Department"] = rng.choice(options)
    for _ in range(30):  # stray spaces in job titles
        i = next(picks)
        raw[i]["JobRole"] = "  " + raw[i]["JobRole"].replace(" ", "  ", 1) + " "
    swapped = 0
    while swapped < 8:  # hire and termination dates typed into the wrong fields
        i = next(picks)
        if raw[i]["TerminationDate"]:
            raw[i]["HireDate"], raw[i]["TerminationDate"] = raw[i]["TerminationDate"], raw[i]["HireDate"]
            swapped += 1
    for _ in range(3):  # IDs typed in a different format
        i = next(picks)
        raw[i]["EmployeeID"] = raw[i]["EmployeeID"].replace("EMP", "emp-")
    for _ in range(15):  # duplicate records from a double export
        i = rng.randrange(len(raw))
        raw.insert(rng.randrange(len(raw)), dict(raw[i]))
    return raw


def clean(raw):
    canonical = {d.lower(): d for d in DEPARTMENTS}
    canonical["hr"] = "Human Resources"
    out, seen = [], set()
    for r in raw:
        r = dict(r)
        flags = []
        r["EmployeeID"] = r["EmployeeID"].strip().upper().replace("-", "")
        r["Department"] = canonical[r["Department"].strip().lower()]
        r["JobRole"] = " ".join(r["JobRole"].split())
        key = tuple(r[c] for c in EMP_COLUMNS)
        if key in seen:
            continue
        seen.add(key)
        if r["TerminationDate"] and r["TerminationDate"] < r["HireDate"]:
            r["HireDate"], r["TerminationDate"] = r["TerminationDate"], r["HireDate"]
            flags.append("Hire/termination dates swapped")
        r["DataQualityFlag"] = flags
        out.append(r)
    for r in out:
        if r["AnnualSalaryUSD"] is None:
            peers = [x["AnnualSalaryUSD"] for x in out if x["JobRole"] == r["JobRole"]
                     and x["AnnualSalaryUSD"] is not None]
            r["AnnualSalaryUSD"] = round(statistics.median(peers) / 100) * 100
            r["DataQualityFlag"].append("Salary imputed (role median)")
        r["DataQualityFlag"] = "; ".join(r["DataQualityFlag"]) or None
    return out


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r[c]) for c in columns})


def write_db(path, tables):
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    for name, (rows, columns, types) in tables.items():
        cols = ", ".join(f'"{c}" {types.get(c, "TEXT")}' for c in columns)
        con.execute(f'CREATE TABLE {name} ({cols})')
        con.executemany(f'INSERT INTO {name} VALUES ({", ".join("?" for _ in columns)})',
                        [[r.get(c) for c in columns] for r in rows])
    con.executescript((ROOT / "sql" / "00_create_views.sql").read_text())
    con.commit()
    con.close()


def segment_rate(rows, keep):
    """2025 leaving rate among critical-team employees employed at any point in 2025."""
    pop = [r for r in rows if DEPARTMENTS[r["Department"]][0] and r["HireDate"] <= "2025-12-31"
           and (r["TerminationDate"] is None or r["TerminationDate"] >= "2025-01-01") and keep(r)]
    left = sum(1 for r in pop if r["TerminationDate"] and r["TerminationDate"][:4] == "2025")
    return left / len(pop) if pop else 0


def acceptable(rows):
    crit = attrition_rates(rows, True)
    rest = attrition_rates(rows, False)
    extra = replacement_cost(rows, 2025) - replacement_cost(rows, 2024)
    active = sum(1 for r in rows if r["TerminationDate"] is None)
    if not (0.215 <= crit[2025]["rate"] < 0.225 and 0.135 <= crit[2024]["rate"] < 0.145
            and 0.115 <= crit[2023]["rate"] < 0.125 and all(0.12 <= rest[y]["rate"] < 0.15 for y in rest)
            and 1_760_000 <= extra <= 1_840_000 and 1150 <= active <= 1250):
        return False
    # Factors designed to have no effect must not show a gap by chance
    onsite = lambda r: r["WorkMode"] != "Remote"
    gender_gap = abs(segment_rate(rows, lambda r: r["Gender"] == "Female")
                     - segment_rate(rows, lambda r: r["Gender"] == "Male"))
    commute_gap = abs(segment_rate(rows, lambda r: onsite(r) and r["CommuteMiles"] > 20)
                      - segment_rate(rows, lambda r: onsite(r) and r["CommuteMiles"] <= 20))
    reasons = {}
    for r in rows:
        if DEPARTMENTS[r["Department"]][0] and r["TerminationDate"] and r["TerminationDate"][:4] == "2025":
            reasons[r["ExitReason"]] = reasons.get(r["ExitReason"], 0) + 1
    top = max(reasons, key=reasons.get)
    if not (gender_gap < 0.025 and commute_gap < 0.03 and top == "Burnout & Workload"):
        return False
    # Designed patterns must be clearly visible
    tenured = lambda r: (date.fromisoformat(r["TerminationDate"] or "2025-12-31")
                         - date.fromisoformat(r["HireDate"])).days > 730
    compa = lambda r: r["AnnualSalaryUSD"] / r["MarketMedianSalaryUSD"]
    senior = lambda r: r["JobLevel"] in ("L3", "L4", "L5")
    ratio = lambda a, b: segment_rate(rows, a) / max(segment_rate(rows, b), 1e-9)
    hot = lambda r: r["ManagerID"] in ("MGR-ENG-03", "MGR-ENG-08")
    return (ratio(lambda r: r["MonthlyOvertimeHours"] > 20, lambda r: r["MonthlyOvertimeHours"] <= 20) >= 2.0
            and ratio(lambda r: tenured(r) and r["MonthsSinceLastPromotion"] > 24,
                      lambda r: tenured(r) and r["MonthsSinceLastPromotion"] <= 24) >= 1.8
            and ratio(lambda r: senior(r) and compa(r) < 0.9, lambda r: senior(r) and compa(r) >= 0.9) >= 1.8
            and ratio(lambda r: not senior(r) and compa(r) < 0.9, lambda r: not senior(r) and compa(r) >= 0.9) <= 1.2
            and ratio(lambda r: r["Department"] == "Engineering" and hot(r),
                      lambda r: r["Department"] == "Engineering" and not hot(r)) >= 1.8)


def main():
    scales = {c: {y: 0.01 for y in (2023, 2024, 2025)} for c in (True, False)}
    # Seeds before 1449 were checked and fail at least one target; starting here keeps runs fast.
    for seed in range(1449, 4000):
        DEPARTMENTS_MANAGERS.clear()
        sim = Sim(seed, scales).run()
        rows = to_rows(sim)
        if acceptable(rows):
            break
    else:
        raise SystemExit("No seed met the targets; adjust assumptions.")

    managers = list(sim.managers.values())
    for m in managers:
        m["SpanOfControl"] = sum(1 for r in rows if r["ManagerID"] == m["ManagerID"] and r["TerminationDate"] is None)
    dept_rows = [{"Department": d, "IsCriticalProductTeam": "Yes" if v[0] else "No",
                  "ReplacementCostMultiplier": v[2], "AvgTimeToFillDays": v[3]} for d, v in DEPARTMENTS.items()]
    mgr_cols = ["ManagerID", "ManagerName", "Department", "ManagerTenureYears", "SpanOfControl"]
    dept_cols = ["Department", "IsCriticalProductTeam", "ReplacementCostMultiplier", "AvgTimeToFillDays"]

    raw = make_raw(rows)
    cleaned = clean(raw)

    write_csv(DATA / "raw" / "employees_raw.csv", raw, EMP_COLUMNS)
    write_csv(DATA / "raw" / "departments.csv", dept_rows, dept_cols)
    write_csv(DATA / "raw" / "managers.csv", managers, mgr_cols)
    write_csv(DATA / "clean" / "employees_clean.csv", cleaned, EMP_COLUMNS + ["DataQualityFlag"])
    write_csv(DATA / "clean" / "departments.csv", dept_rows, dept_cols)
    write_csv(DATA / "clean" / "managers.csv", managers, mgr_cols)

    ints = {c: "INTEGER" for c in ["Age", "CommuteMiles", "AnnualSalaryUSD", "MarketMedianSalaryUSD",
                                   "MonthlyOvertimeHours", "JobSatisfaction", "WorkLifeBalance", "EngagementScore",
                                   "PerformanceRating", "PromotionsLast3Years", "MonthsSinceLastPromotion",
                                   "TrainingHoursLastYear", "AvgTimeToFillDays", "SpanOfControl"]}
    ints.update({"ReplacementCostMultiplier": "REAL", "ManagerTenureYears": "REAL"})
    write_db(DATA / "nimbustech.db", {
        "employees": (cleaned, EMP_COLUMNS + ["DataQualityFlag"], ints),
        "employees_raw": (raw, EMP_COLUMNS, ints),
        "departments": (dept_rows, dept_cols, ints),
        "managers": (managers, mgr_cols, ints),
    })

    crit, rest = attrition_rates(cleaned, True), attrition_rates(cleaned, False)
    print(f"seed={seed}  raw rows={len(raw)}  clean rows={len(cleaned)}  "
          f"active={sum(1 for r in cleaned if r['TerminationDate'] is None)}")
    for y in (2023, 2024, 2025):
        print(f"{y}: critical {crit[y]['rate']:.1%} ({crit[y]['leavers']} of ~{crit[y]['avg_hc']:.0f})  "
              f"rest {rest[y]['rate']:.1%}  critical cost ${replacement_cost(cleaned, y):,.0f}")
    print(f"Extra cost 2025 vs 2024: ${replacement_cost(cleaned, 2025) - replacement_cost(cleaned, 2024):,.0f}")


if __name__ == "__main__":
    main()
