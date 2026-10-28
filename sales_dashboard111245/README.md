# Sales Data Analysis Dashboard

A Flask + Pandas + MySQL backend with a vanilla JS / Chart.js front end. Amounts are shown in Indian rupees (₹).

## Run it in VS Code

1. Open this folder in VS Code (File > Open Folder).
2. Open the terminal (Ctrl + `) and create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
3. Install packages: `pip install -r requirements.txt`
4. Start the app: `python app.py`
5. Open http://127.0.0.1:5000 and sign in (default `admin` / `admin123`)

The sample data (about 7,000 orders for 2024-2025) is created automatically on first run.
Run `python data_generator.py` to regenerate it, or replace `data/sales_data.csv` with your own file
that has the same columns.

## Features

- KPI cards with change versus the previous period of equal length
- Filters for date range, region and category, plus quick presets
- Revenue and profit trend by day, week or month, with a 3-month linear forecast
- Category, region, product and channel charts
- Auto-generated insights
- Searchable, sortable, paginated orders table
- CSV export of the filtered data
- Dark and light themes
- Login page with session-protected dashboard and API
- Rupee formatting (₹, lakh/crore style)

## Structure

    app.py               Flask server and JSON API
    data_generator.py    Creates the sample dataset
    templates/index.html Dashboard layout
    templates/login.html Login page
    static/css/style.css Styles and themes
    static/js/dashboard.js Charts, filters, table logic
    data/sales_data.csv  Dataset (generated)

## API

    /api/filters   /api/summary   /api/trend   /api/breakdown
    /api/insights  /api/orders    /api/export

All accept `start`, `end`, `region` and `category` query parameters.

## Ideas to extend

- Upload your own CSV from the page
- Swap the linear forecast for statsmodels or Prophet
- Store users in MySQL instead of a single demo account

## Login and currency settings

Set these environment variables before `python app.py` to change the defaults:

    DASHBOARD_USER       login name (default admin)
    DASHBOARD_PASSWORD   password (default admin123)
    SECRET_KEY           session signing key (set your own)

Stored data was generated in dollars, so `INR_RATE` in `app.py` (default 83) converts
amounts to rupees when loaded. Set it to 1 if your table already holds rupee values.
