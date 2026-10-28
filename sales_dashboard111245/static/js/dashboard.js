/* SalesPulse dashboard: charts, filters, orders table. All money is in rupees. */

const state = { granularity: "month", page: 1, sort: "date", dir: "desc", q: "" };
const charts = {};
const $ = (id) => document.getElementById(id);

/* ---------- Formatting (Indian number system) ---------- */
const inrFull = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const numIN = new Intl.NumberFormat("en-IN");

function inr(n) { return inrFull.format(n || 0); }

// Compact form for KPI cards and chart axes: ₹1.2 Cr, ₹4.5 L, ₹12.3 K
function inrShort(n) {
  const v = Math.abs(n || 0), sign = n < 0 ? "-" : "";
  if (v >= 1e7) return `${sign}₹${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${sign}₹${(v / 1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${sign}₹${(v / 1e3).toFixed(1)} K`;
  return `${sign}₹${v.toFixed(0)}`;
}

/* ---------- Theme ---------- */
function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function applyChartTheme() {
  Chart.defaults.color = cssVar("--muted");
  Chart.defaults.borderColor = cssVar("--border");
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
}

function palette() {
  return ["#5b5bf0", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#ec4899"];
}

$("themeBtn").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (e) {}
  applyChartTheme();
  refresh();
});

/* ---------- API ---------- */
function params(extra = {}) {
  const p = new URLSearchParams({
    start: $("start").value,
    end: $("end").value,
    region: $("region").value,
    category: $("category").value,
    ...extra,
  });
  return p.toString();
}

async function api(path, extra) {
  const res = await fetch(`${path}?${params(extra)}`);
  if (res.status === 401) { window.location = "/login"; throw new Error("Not signed in"); }
  return res.json();
}

/* ---------- Charts ---------- */
function draw(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart($(id), config);
}

const moneyTooltip = { callbacks: { label: (c) => ` ${c.dataset.label ? c.dataset.label + ": " : ""}${inr(c.parsed.y ?? c.parsed.x ?? c.parsed)}` } };
const moneyAxis = { ticks: { callback: (v) => inrShort(v) }, grid: { color: cssVar("--border") } };

function barChart(id, data, horizontal = false) {
  draw(id, {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [
        { label: "Revenue", data: data.revenue, backgroundColor: "#5b5bf0", borderRadius: 6 },
        { label: "Profit", data: data.profit, backgroundColor: "#14b8a6", borderRadius: 6 },
      ],
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" }, tooltip: moneyTooltip },
      scales: horizontal
        ? { x: moneyAxis, y: { grid: { display: false } } }
        : { y: moneyAxis, x: { grid: { display: false } } },
    },
  });
}

function doughnut(id, data) {
  draw(id, {
    type: "doughnut",
    data: { labels: data.labels, datasets: [{ data: data.revenue, backgroundColor: palette(), borderWidth: 0 }] },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "62%",
      plugins: {
        legend: { position: "bottom" },
        tooltip: { callbacks: { label: (c) => ` ${c.label}: ${inr(c.parsed)}` } },
      },
    },
  });
}

/* ---------- Loaders ---------- */
function setKpi(key, text, change) {
  $(`k-${key}`).textContent = text;
  const el = $(`d-${key}`);
  if (change === null || change === undefined) { el.textContent = "no prior period"; el.className = "delta"; return; }
  el.textContent = `${change >= 0 ? "▲" : "▼"} ${Math.abs(change)}% vs previous period`;
  el.className = "delta " + (change >= 0 ? "up" : "down");
}

async function loadSummary() {
  const k = await api("/api/summary");
  setKpi("revenue", inrShort(k.revenue.value), k.revenue.change);
  setKpi("profit", inrShort(k.profit.value), k.profit.change);
  setKpi("orders", numIN.format(k.orders.value), k.orders.change);
  setKpi("aov", inr(k.aov.value), k.aov.change);
  setKpi("margin", `${k.margin.value.toFixed(1)}%`, k.margin.change);
  $("k-revenue").title = inr(k.revenue.value);
  $("k-profit").title = inr(k.profit.value);
}

async function loadTrend() {
  const t = await api("/api/trend", { granularity: state.granularity });
  draw("trendChart", {
    type: "line",
    data: {
      labels: t.labels,
      datasets: [
        { label: "Revenue", data: t.revenue, borderColor: "#5b5bf0", backgroundColor: "rgba(91,91,240,.12)", fill: true, tension: .35, pointRadius: 2 },
        { label: "Profit", data: t.profit, borderColor: "#14b8a6", tension: .35, pointRadius: 2 },
        { label: "Forecast", data: t.forecast, borderColor: "#f59e0b", borderDash: [6, 5], tension: .35, pointRadius: 3 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, spanGaps: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom" }, tooltip: moneyTooltip },
      scales: { y: moneyAxis, x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } } },
    },
  });
}

async function loadBreakdown() {
  const b = await api("/api/breakdown");
  barChart("categoryChart", b.category);
  barChart("regionChart", b.region);
  doughnut("channelChart", b.channel);
  barChart("productChart", b.products, true);
  doughnut("segmentChart", b.segment);
}

async function loadInsights() {
  const list = await api("/api/insights");
  $("insights").innerHTML = list.map((t) => `<li>${t}</li>`).join("");
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function loadOrders() {
  const o = await api("/api/orders", { page: state.page, sort: state.sort, dir: state.dir, q: state.q });
  $("ordersBody").innerHTML = o.rows.length
    ? o.rows.map((r) => `
        <tr>
          <td>${esc(r.order_id)}</td><td>${esc(r.date)}</td><td>${esc(r.region)}</td>
          <td>${esc(r.category)}</td><td>${esc(r.product)}</td>
          <td class="num">${numIN.format(r.quantity)}</td>
          <td class="num">${inr(r.revenue)}</td><td class="num">${inr(r.profit)}</td>
        </tr>`).join("")
    : `<tr><td colspan="8" class="empty">No orders match your filters.</td></tr>`;

  $("pageInfo").textContent = `Page ${o.page} of ${o.pages} · ${numIN.format(o.total)} orders`;
  $("prevBtn").disabled = o.page <= 1;
  $("nextBtn").disabled = o.page >= o.pages;
  state.page = o.page;

  document.querySelectorAll("#ordersTable th").forEach((th) => {
    th.classList.toggle("sorted", th.dataset.sort === state.sort);
    th.classList.toggle("desc", th.dataset.sort === state.sort && state.dir === "desc");
  });
}

function updateRangeLabel() {
  const fmt = (d) => new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  $("rangeLabel").textContent = `${fmt($("start").value)} – ${fmt($("end").value)} · all amounts in ₹`;
}

async function refresh() {
  updateRangeLabel();
  await Promise.all([loadSummary(), loadTrend(), loadBreakdown(), loadInsights(), loadOrders()]);
}

function resetAndRefresh() { state.page = 1; refresh(); }

/* ---------- Init ---------- */
function setPreset(p, minDate, maxDate) {
  const end = new Date(maxDate);
  const start = p === "all" ? new Date(minDate) : new Date(end.getTime() - Number(p) * 86400000);
  const iso = (d) => d.toISOString().slice(0, 10);
  $("start").value = iso(start < new Date(minDate) ? new Date(minDate) : start);
  $("end").value = iso(end);
}

async function init() {
  applyChartTheme();
  const f = await (await fetch("/api/filters")).json();

  f.regions.forEach((r) => $("region").add(new Option(r, r)));
  f.categories.forEach((c) => $("category").add(new Option(c, c)));
  $("start").value = f.min_date;
  $("end").value = f.max_date;
  $("start").min = $("end").min = f.min_date;
  $("start").max = $("end").max = f.max_date;

  ["start", "end", "region", "category"].forEach((id) => $(id).addEventListener("change", resetAndRefresh));

  $("presets").addEventListener("click", (e) => {
    const b = e.target.closest("[data-preset]");
    if (!b) return;
    document.querySelectorAll("#presets .chip").forEach((c) => c.classList.toggle("active", c === b));
    setPreset(b.dataset.preset, f.min_date, f.max_date);
    resetAndRefresh();
  });

  $("granularity").addEventListener("click", (e) => {
    const b = e.target.closest("[data-g]");
    if (!b) return;
    state.granularity = b.dataset.g;
    document.querySelectorAll("#granularity button").forEach((x) => x.classList.toggle("active", x === b));
    loadTrend();
  });

  let timer;
  $("search").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => { state.q = e.target.value; state.page = 1; loadOrders(); }, 250);
  });

  document.querySelectorAll("#ordersTable th").forEach((th) =>
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      state.dir = state.sort === col && state.dir === "desc" ? "asc" : "desc";
      state.sort = col;
      state.page = 1;
      loadOrders();
    })
  );

  $("prevBtn").addEventListener("click", () => { state.page--; loadOrders(); });
  $("nextBtn").addEventListener("click", () => { state.page++; loadOrders(); });
  $("exportBtn").addEventListener("click", () => { window.location = `/api/export?${params()}`; });

  refresh();
}

init();
