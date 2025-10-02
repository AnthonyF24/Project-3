from __future__ import annotations
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import json
from datetime import date, datetime
import uuid

app = Flask(__name__, static_folder="static", static_url_path="/")

DATA_PATH = Path("state.json")

def load_state():
    if not DATA_PATH.exists():
        return {"budgets": [], "transactions": [], "settings": {"currency": "EUR", "rollover_enabled": False}}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    tmp = DATA_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(DATA_PATH)

def validate_iso_date(s: str) -> str:
    # Try DD-MM-YYYY format first
    try:
        parsed_date = datetime.strptime(s, "%d-%m-%Y")
        return parsed_date.strftime("%Y-%m-%d")  # Convert to ISO format for storage
    except ValueError:
        # Fallback to YYYY-MM-DD for backward compatibility
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            raise ValueError("Date must be DD-MM-YYYY or YYYY-MM-DD")

def month_key(d: str) -> str:
    # d is YYYY-MM-DD
    return d[:7]

def format_date_for_display(iso_date: str) -> str:
    """Convert YYYY-MM-DD to DD-MM-YYYY for display"""
    try:
        parsed_date = datetime.strptime(iso_date, "%Y-%m-%d")
        return parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        return iso_date  # Return as-is if parsing fails

def get_budget_map(state, month):
    for b in state["budgets"]:
        if b["month"] == month:
            return b["limits"]
    return {}

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# --- Budgets ---
@app.get("/api/budgets/<month>")
def get_budget(month):
    state = load_state()
    limits = get_budget_map(state, month)
    return jsonify({"month": month, "limits": limits})

@app.post("/api/budgets/<month>")
def set_budget(month):
    payload = request.get_json(force=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Payload must be an object of {category: limit}"}), 400
    # basic validation
    for k, v in payload.items():
        if not isinstance(k, str) or not k.strip():
            return jsonify({"error": "Category names must be non-empty strings"}), 400
        try:
            val = float(v)
            if val < 0:
                return jsonify({"error": f"Limit for {k} must be >= 0"}), 400
            payload[k] = val
        except Exception:
            return jsonify({"error": f"Limit for {k} must be a number"}), 400

    state = load_state()
    # upsert month
    for b in state["budgets"]:
        if b["month"] == month:
            b["limits"] = payload
            save_state(state)
            return jsonify({"ok": True})
    state["budgets"].append({"month": month, "limits": payload})
    save_state(state)
    return jsonify({"ok": True})

# --- Transactions ---
@app.get("/api/transactions")
def list_transactions():
    state = load_state()
    month = request.args.get("month")
    category = request.args.get("category")
    q = request.args.get("q", "").lower().strip()

    txs = state["transactions"]
    if month:
        txs = [t for t in txs if month_key(t["date"]) == month]
    if category:
        txs = [t for t in txs if t["category"].lower() == category.lower()]
    if q:
        txs = [t for t in txs if q in t.get("description", "").lower()]

    # Format dates for display
    for tx in txs:
        tx["date"] = format_date_for_display(tx["date"])

    return jsonify({"transactions": txs})

@app.post("/api/transactions")
def add_transaction():
    data = request.get_json(force=True) or {}
    # Validate
    try:
        d = validate_iso_date(str(data.get("date")))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        amount = float(data.get("amount"))
    except Exception:
        return jsonify({"error": "Amount must be a number"}), 400

    ttype = data.get("type")
    if ttype not in ("expense", "income"):
        return jsonify({"error": "type must be 'expense' or 'income'"}), 400

    category = (data.get("category") or "").strip()
    if not category:
        return jsonify({"error": "category is required"}), 400

    desc = (data.get("description") or "").strip()
    if ttype == "expense" and amount > 0:
        amount = -amount  # store expenses negative

    tx = {
        "id": data.get("id") or f"tx_{uuid.uuid4().hex[:8]}",
        "date": d,
        "amount": amount,
        "type": ttype,
        "category": category,
        "description": desc,
        "tags": data.get("tags") or [],
        "notes": data.get("notes") or ""
    }

    state = load_state()
    if any(t["id"] == tx["id"] for t in state["transactions"]):
        return jsonify({"error": "Duplicate transaction id"}), 400

    state["transactions"].append(tx)
    save_state(state)
    
    # Format the date for the response
    tx["date"] = format_date_for_display(tx["date"])
    return jsonify({"ok": True, "transaction": tx}), 201

# --- Reports ---
@app.get("/api/reports/<month>")
def report_month(month):
    state = load_state()
    limits = get_budget_map(state, month)
    txs = [t for t in state["transactions"] if month_key(t["date"]) == month]

    income = sum(t["amount"] for t in txs if t["amount"] > 0)
    expenses = -sum(t["amount"] for t in txs if t["amount"] < 0)
    net = income - expenses

    # category aggregation
    cat_actual = {}
    for t in txs:
        if t["amount"] < 0:
            cat_actual[t["category"]] = cat_actual.get(t["category"], 0.0) + (-t["amount"])

    # simple burn-rate forecast
    year, mon = map(int, month.split("-"))
    from calendar import monthrange
    days_in_month = monthrange(year, mon)[1]
    today = date.today()
    days_elapsed = min(today.day, days_in_month) if (today.year == year and today.month == mon) else days_in_month
    burn_rate = (expenses / max(days_elapsed, 1)) if expenses else 0.0
    forecast_expenses = burn_rate * days_in_month

    breakdown = []
    for cat, actual in sorted(cat_actual.items(), key=lambda x: x[1], reverse=True):
        limit = float(limits.get(cat, 0))
        remaining = limit - actual if limit else None
        breakdown.append({
            "category": cat,
            "limit": limit,
            "actual": round(actual, 2),
            "remaining": round(remaining, 2) if remaining is not None else None
        })

    return jsonify({
        "month": month,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net": round(net, 2),
        "burn_rate": round(burn_rate, 2),
        "forecast_expenses": round(forecast_expenses, 2),
        "breakdown": breakdown
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
