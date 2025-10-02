# Project-3
# Budget & Expense Manager

A Python-first command-line and web-based budgeting tool.  
This project was built as **Portfolio Project 3 (Python Essentials)** for Code Institute, using the [python-essentials-template](https://github.com/Code-Institute-Org/python-essentials-template).  

The application allows users to set monthly budgets, log expenses/income, view transaction history, and generate reports with forecasts — all managed by Python, with a simple interactive web page for ease of use.

---

## Table of Contents
- [Project Purpose](#project-purpose)
- [User Stories](#user-stories)
- [Features](#features)
- [Data Model](#data-model)
- [Technologies Used](#technologies-used)
- [Testing](#testing)
- [Deployment](#deployment)
- [AI Usage & Attribution](#ai-usage--attribution)
- [Credits](#credits)

---

## Project Purpose

The purpose of this project is to demonstrate the ability to build a **Python-driven application** that manages a dataset and exposes functionality through a hosted interface.  

- **Target users:** Students, individuals, or freelancers who want a simple budgeting tool.  
- **Goal:** Provide clear insight into monthly spending, help control overspending, and allow data persistence with easy import/export.  

---

## User Stories

1. As a user, I want to **set a monthly budget** by category.  
2. As a user, I want to **log expenses and income** with descriptions.  
3. As a user, I want to **see my transaction history** filtered by month or category.  
4. As a user, I want to **generate reports** showing income, expenses, net total, and forecasts.  
5. As a user, I want to **import/export my data** in CSV/JSON formats.  

---

## Features

- **Set monthly budgets** with categories and spending limits.  
- **Add transactions** (income or expenses) with date, description, and category.  
- **Transaction listing** with filters for category and month.  
- **Reports:**  
  - Income vs Expenses  
  - Net balance  
  - Category breakdown (budget vs actual vs remaining)  
  - Burn rate & forecasted month-end spend  
- **Input validation:**  
  - Dates in `YYYY-MM-DD` format  
  - Amounts must be numeric  
  - Categories must be valid  
  - Duplicate transactions prevented  
- **Import/Export:** Transactions and budgets via JSON/CSV.  
- **Interactive Web Page:** HTML/CSS/JS frontend powered by a Flask backend.  

---

## Data Model

All data is stored in a JSON file (`state.json`):

```json
{
  "budgets": [
    { "month": "2025-10", "limits": { "Rent": 1200, "Groceries": 300 } }
  ],
  "transactions": [
    {
      "id": "tx_001",
      "date": "2025-10-02",
      "amount": -45.90,
      "type": "expense",
      "category": "Groceries",
      "description": "Lidl shop"
    }
  ],
  "settings": {
    "currency": "EUR",
    "rollover_enabled": false
  }
}
