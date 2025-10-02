const $ = (sel) => document.querySelector(sel);

// Set today's date as default in the date picker
function setTodayAsDefault() {
  const today = new Date();
  const todayString = today.toISOString().split('T')[0]; // YYYY-MM-DD format
  $("#tx-date").value = todayString;
}

// Initialize the date picker with today's date when page loads
document.addEventListener('DOMContentLoaded', setTodayAsDefault);

function addBudgetRow(cat = "", limit = "") {
  const wrap = document.createElement("div");
  wrap.className = "row";
  wrap.innerHTML = `
    <input class="cat" placeholder="Category" value="${cat}"/>
    <input class="lim" type="number" step="0.01" placeholder="Limit" value="${limit}"/>
    <button class="del">Remove</button>
  `;
  wrap.querySelector(".del").onclick = () => wrap.remove();
  $("#budgets").appendChild(wrap);
}

$("#add-cat").onclick = () => addBudgetRow();

$("#save-budget").onclick = async () => {
  const month = $("#month").value.trim();
  if (!month) { $("#budget-msg").textContent = "Enter month (MM-YYYY)"; return; }
  
  // Convert MM-YYYY to YYYY-MM for backend storage
  const monthParts = month.split('-');
  if (monthParts.length !== 2) {
    $("#budget-msg").textContent = "Invalid month format. Use MM-YYYY";
    return;
  }
  const backendMonth = `${monthParts[1]}-${monthParts[0].padStart(2, '0')}`;
  
  const cats = [...document.querySelectorAll("#budgets .row")];
  const payload = {};
  for (const r of cats) {
    const c = r.querySelector(".cat").value.trim();
    const l = r.querySelector(".lim").value.trim();
    if (c) payload[c] = l || "0";
  }
  const res = await fetch(`/api/budgets/${backendMonth}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  $("#budget-msg").textContent = data.ok ? "Budget saved." : (data.error || "Error");
};

$("#add-tx").onclick = async () => {
  const dateValue = $("#tx-date").value.trim();
  if (!dateValue) {
    $("#tx-msg").textContent = "Please select a date";
    return;
  }
  
  // Convert YYYY-MM-DD from date picker to DD-MM-YYYY for backend
  const dateParts = dateValue.split('-');
  const formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;
  
  const payload = {
    date: formattedDate,
    amount: $("#tx-amount").value.trim(),
    type: $("#tx-type").value,
    category: $("#tx-category").value.trim(),
    description: $("#tx-desc").value.trim()
  };
  const res = await fetch("/api/transactions", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  $("#tx-msg").textContent = data.ok ? "Transaction added." : (data.error || "Error");
  if (data.ok) {
    loadTransactions();
    // Clear the form
    $("#tx-date").value = "";
    $("#tx-amount").value = "";
    $("#tx-category").value = "";
    $("#tx-desc").value = "";
  }
};

async function loadTransactions() {
  const month = $("#month").value.trim();
  const cat = $("#filter-category").value.trim();
  const qs = new URLSearchParams();
  
  // Convert MM-YYYY to YYYY-MM for backend
  if (month) {
    const monthParts = month.split('-');
    if (monthParts.length === 2) {
      const backendMonth = `${monthParts[1]}-${monthParts[0].padStart(2, '0')}`;
      qs.set("month", backendMonth);
    }
  }
  if (cat) qs.set("category", cat);
  
  const res = await fetch(`/api/transactions?${qs.toString()}`);
  const data = await res.json();
  const tbody = $("#tx-table tbody");
  tbody.innerHTML = "";
  for (const t of data.transactions.slice(-200)) { // simple cap
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${t.date}</td>
      <td>${t.type}</td>
      <td>${t.category}</td>
      <td>${t.description || ""}</td>
      <td style="text-align:right">${Number(t.amount).toFixed(2)}</td>`;
    tbody.appendChild(tr);
  }
}

$("#load-txs").onclick = loadTransactions;

$("#load-report").onclick = async () => {
  const month = $("#month").value.trim();
  if (!month) { $("#report").textContent = "Enter month (MM-YYYY)"; return; }
  
  // Convert MM-YYYY to YYYY-MM for backend
  const monthParts = month.split('-');
  if (monthParts.length !== 2) {
    $("#report").textContent = "Invalid month format. Use MM-YYYY";
    return;
  }
  const backendMonth = `${monthParts[1]}-${monthParts[0].padStart(2, '0')}`;
  
  const res = await fetch(`/api/reports/${backendMonth}`);
  const r = await res.json();
  const lines = [];
  lines.push(`Month: ${month}`); // Display in user-friendly format
  lines.push(`Income: ${r.income}`);
  lines.push(`Expenses: ${r.expenses}`);
  lines.push(`Net: ${r.net}`);
  lines.push(`Burn Rate: ${r.burn_rate}`);
  lines.push(`Forecast Expenses: ${r.forecast_expenses}`);
  lines.push("");
  lines.push("Category Breakdown (limit / actual / remaining):");
  for (const row of r.breakdown) {
    lines.push(`- ${row.category}: ${row.limit} / ${row.actual} / ${row.remaining ?? "-"}`);
  }
  $("#report").textContent = lines.join("\n");
};

// Load any existing month budget on month change
$("#month").addEventListener("change", async () => {
  $("#budgets").innerHTML = "";
  const m = $("#month").value.trim();
  if (!m) return;
  
  // Convert MM-YYYY to YYYY-MM for backend
  const monthParts = m.split('-');
  if (monthParts.length !== 2) return;
  const backendMonth = `${monthParts[1]}-${monthParts[0].padStart(2, '0')}`;
  
  const res = await fetch(`/api/budgets/${backendMonth}`);
  const data = await res.json();
  const limits = data.limits || {};
  if (Object.keys(limits).length === 0) addBudgetRow();
  else Object.entries(limits).forEach(([c, l]) => addBudgetRow(c, l));
  loadTransactions();
});
