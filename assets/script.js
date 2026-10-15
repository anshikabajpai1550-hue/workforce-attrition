// Figures come from the SQL analysis in /sql (2025, product teams unless noted).
const COLORS = { accent: "#c8461b", ink: "#14213d", neutral: "#b9b0a2", rule: "#d9d0c1", muted: "#6f6a60" };
const BUSINESS_CASE = { currentRate: 21.7, avgHeadcount: 336, costPerLeaver: 64068 };

const pct = (v) => `${v}%`;

function baseOptions(extra = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 900, easing: "easeOutQuart" },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (c) => ` ${c.dataset.label ? c.dataset.label + ": " : ""}${c.formattedValue}%` } },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: COLORS.ink, font: { family: "IBM Plex Sans", size: 13 } } },
      y: {
        beginAtZero: true,
        grid: { color: COLORS.rule },
        border: { display: false },
        ticks: { color: COLORS.muted, callback: pct, font: { family: "IBM Plex Sans" } },
      },
    },
    ...extra,
  };
}

function bars(labels, values, highlightIndexes, extra) {
  return {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: values.map((_, i) => (highlightIndexes.includes(i) ? COLORS.accent : COLORS.neutral)),
        borderRadius: 2,
        maxBarThickness: 64,
      }],
    },
    options: baseOptions(extra),
  };
}

const charts = {
  chartTrend: () => ({
    type: "line",
    data: {
      labels: ["2023", "2024", "2025"],
      datasets: [
        { label: "Product teams", data: [11.9, 14.0, 21.7], borderColor: COLORS.accent, backgroundColor: COLORS.accent, borderWidth: 3, pointRadius: 5, tension: 0.25 },
        { label: "Rest of company", data: [12.9, 13.4, 14.0], borderColor: COLORS.neutral, backgroundColor: COLORS.neutral, borderWidth: 3, pointRadius: 5, tension: 0.25 },
      ],
    },
    options: baseOptions({
      plugins: {
        legend: { display: true, position: "bottom", labels: { usePointStyle: true, boxWidth: 8, color: COLORS.ink, font: { family: "IBM Plex Sans" } } },
        tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.formattedValue}%` } },
      },
    }),
  }),
  chartOvertime: () => bars(["0–10 hrs", "11–20 hrs", "Over 20 hrs"], [10.3, 13.4, 27.1], [2]),
  chartPromo: () => bars(["Promoted in last 2 yrs", "No promotion in 2+ yrs"], [5.9, 19.6], [1]),
  chartPay: () => bars(["Paid at market", "Paid 10%+ below market"], [9.9, 40.0], [1]),
  chartTenure: () => bars(["Under 1 yr", "1–2 yrs", "2–4 yrs", "4+ yrs"], [25.8, 8.9, 13.2, 18.0], [0]),
  chartManagers: () => {
    const values = [51.9, 42.4, 20.0, 17.4, 17.2, 14.3, 10.0, 8.3, 7.7, 7.4, 7.1, 5.6, 4.2];
    const labels = values.map((_, i) => `Manager ${String.fromCharCode(65 + i)}`);
    const cfg = bars(labels, values, [0, 1], { indexAxis: "y" });
    cfg.options.scales = {
      x: { beginAtZero: true, grid: { color: COLORS.rule }, border: { display: false }, ticks: { color: COLORS.muted, callback: pct } },
      y: { grid: { display: false }, ticks: { color: COLORS.ink, font: { family: "IBM Plex Sans", size: 12 } } },
    };
    cfg.data.datasets[0].maxBarThickness = 20;
    return cfg;
  },
};

function drawChart(canvas) {
  if (!window.Chart || canvas.dataset.drawn) return;
  canvas.dataset.drawn = "1";
  new Chart(canvas, charts[canvas.id]());
}

function updateBusinessCase() {
  const target = parseFloat(document.getElementById("target").value);
  const avoided = ((BUSINESS_CASE.currentRate - target) / 100) * BUSINESS_CASE.avgHeadcount;
  const savings = Math.max(0, avoided) * BUSINESS_CASE.costPerLeaver;
  document.getElementById("targetOut").textContent = `${target.toFixed(1)}%`;
  document.getElementById("leaversOut").textContent = Math.max(0, Math.round(avoided));
  document.getElementById("savingsOut").textContent =
    savings >= 1e6 ? `$${(savings / 1e6).toFixed(2)}M` : `$${Math.round(savings / 1000)}K`;
}

document.addEventListener("DOMContentLoaded", () => {
  const canvases = document.querySelectorAll("canvas[id]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!("IntersectionObserver" in window) || reducedMotion) {
    canvases.forEach(drawChart);
  } else {
    document.documentElement.classList.add("can-animate");
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        entry.target.querySelectorAll("canvas[id]").forEach(drawChart);
        if (entry.target.tagName === "CANVAS") drawChart(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.12 });

    document.querySelectorAll(".finding, .actions li, .steps li, .reveal:not(.hero .reveal)").forEach((el) => io.observe(el));
    canvases.forEach((c) => io.observe(c));

    // Hero animates on load with a short stagger, independent of scrolling
    document.querySelectorAll(".hero .reveal").forEach((el, i) => {
      el.style.transitionDelay = `${i * 90}ms`;
      requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("is-in")));
    });
  }

  const slider = document.getElementById("target");
  slider.addEventListener("input", updateBusinessCase);
  updateBusinessCase();
});
