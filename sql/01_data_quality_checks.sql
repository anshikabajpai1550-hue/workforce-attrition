-- Business question: Can we trust the HR export before we analyze it?
-- Runs against the RAW table (employees_raw), before cleaning.

-- Duplicate records (same employee exported twice)
SELECT COUNT(*) - COUNT(DISTINCT UPPER(REPLACE(TRIM(EmployeeID), '-', ''))) AS DuplicateRows
FROM employees_raw;

-- Missing salaries
SELECT COUNT(*) AS MissingSalary
FROM employees_raw
WHERE AnnualSalaryUSD IS NULL;

-- Department spelled in different ways
SELECT Department, COUNT(*) AS Employees
FROM employees_raw
GROUP BY Department
ORDER BY Department;

-- People who appear to leave before they were hired (dates entered in the wrong fields)
SELECT EmployeeID, HireDate, TerminationDate
FROM employees_raw
WHERE TerminationDate < HireDate;

-- Job titles with extra spaces
SELECT COUNT(*) AS TitlesWithExtraSpaces
FROM employees_raw
WHERE JobRole <> TRIM(JobRole) OR JobRole LIKE '%  %';

-- Employee IDs in the wrong format
SELECT EmployeeID
FROM employees_raw
WHERE EmployeeID NOT GLOB 'EMP[0-9]*';
