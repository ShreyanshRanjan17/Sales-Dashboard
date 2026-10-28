"""Sales Data Analysis Dashboard - Flask backend.

Run: python app.py
Then open http://127.0.0.1:5000
"""

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from flask import (
    Flask, Response, jsonify, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from data_generator import generate

BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "sales_data.csv"

app = Flask(__name__)

# ------------------------------------------------------------
# AUTH + CURRENCY SETTINGS
# ------------------------------------------------------------

# Used to sign the login session cookie. Set SECRET_KEY in your
# environment for anything beyond local use.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Demo login. Override with DASHBOARD_USER / DASHBOARD_PASSWORD.
ADMIN_USER = os.environ.get("DASHBOARD_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get("DASHBOARD_PASSWORD", "admin123")
)

# The stored data was generated in dollars. Amounts are multiplied by
# this rate when loaded, so every chart, table and export shows rupees.
# Set it to 1 if your database already holds rupee values.
INR_RATE = 1.0


def format_inr(amount):
    """Format a number the Indian way, e.g. ₹12,34,567."""
    n = int(round(float(amount)))
    digits = str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        digits = f"{head},{tail}"
    return f"{'-' if n < 0 else ''}₹{digits}"

# ------------------------------------------------------------
# MYSQL CONFIGURATION
# ------------------------------------------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "sales_dashboard",
}

# Change this password if your actual MySQL root password differs.


# ------------------------------------------------------------
# DATABASE CONNECTION
# ------------------------------------------------------------

def get_db_connection():
    """Connect to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


# ------------------------------------------------------------
# CREATE TABLE AND IMPORT CSV DATA
# ------------------------------------------------------------

def initialize_database():
    """Create the sales table and import CSV data if it is empty."""

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                order_id VARCHAR(50) PRIMARY KEY,
                date DATE,
                region VARCHAR(50),
                category VARCHAR(100),
                product VARCHAR(100),
                channel VARCHAR(50),
                segment VARCHAR(50),
                quantity INT,
                unit_price DECIMAL(12, 2),
                discount DECIMAL(5, 2),
                revenue DECIMAL(12, 2),
                profit DECIMAL(12, 2)
            )
        """)

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM sales")
        count = cursor.fetchone()[0]

        # Import the CSV only when the table is empty.
        if count == 0:

            if not DATA_FILE.exists():
                generate(DATA_FILE)

            df = pd.read_csv(DATA_FILE, parse_dates=["date"]).head(500)
            required_columns = [
                "order_id",
                "date",
                "region",
                "category",
                "product",
                "channel",
                "segment",
                "quantity",
                "unit_price",
                "discount",
                "revenue",
                "profit",
            ]

            missing_columns = set(required_columns) - set(df.columns)

            if missing_columns:
                raise ValueError(
                    f"Missing CSV columns: {sorted(missing_columns)}"
                )

            df = df[required_columns].copy()

            # Convert pandas dates and missing values for MySQL.
            df["date"] = pd.to_datetime(
                df["date"], errors="raise"
            ).dt.date

            df = df.astype(object).where(pd.notna(df), None)

            rows = list(df.itertuples(index=False, name=None))

            insert_query = """
                INSERT INTO sales (
                    order_id, date, region, category, product,
                    channel, segment, quantity, unit_price,
                    discount, revenue, profit
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """

            cursor.executemany(insert_query, rows)
            conn.commit()

            print(f"Imported {len(rows)} sales records into MySQL.")

        else:
            print(f"MySQL already contains {count} sales records.")

        cursor.close()

    finally:
        conn.close()


# ------------------------------------------------------------
# LOAD DATA FROM MYSQL
# ------------------------------------------------------------

def load_data() -> pd.DataFrame:
    """Load sales records from MySQL into a pandas DataFrame."""

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                order_id, date, region, category, product,
                channel, segment, quantity, unit_price,
                discount, revenue, profit
            FROM sales
        """)

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        df = pd.DataFrame(rows, columns=columns)

        if df.empty:
            raise ValueError(
                "The sales table is empty. Add sales records before starting."
            )

        df["date"] = pd.to_datetime(df["date"])

        numeric_columns = [
            "quantity",
            "unit_price",
            "discount",
            "revenue",
            "profit",
        ]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Convert dollar amounts to rupees.
        for col in ("unit_price", "revenue", "profit"):
            df[col] = (df[col] * INR_RATE).round(2)

        return df

    finally:
        conn.close()


# Initialize the database before loading dashboard data.
initialize_database()

DF = load_data()

MIN_DATE, MAX_DATE = DF["date"].min(), DF["date"].max()


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def get_range():
    start = pd.to_datetime(request.args.get("start") or MIN_DATE)
    end = pd.to_datetime(request.args.get("end") or MAX_DATE)
    return start, end


def subset(start, end):
    """Filter sales by date, region, and category."""

    df = DF[(DF["date"] >= start) & (DF["date"] <= end)]

    for col in ("region", "category"):
        value = request.args.get(col)

        if value and value != "All":
            df = df[df[col] == value]

    return df


def totals(df):
    revenue = df["revenue"].sum()
    profit = df["profit"].sum()
    orders = len(df)

    return {
        "revenue": float(revenue),
        "profit": float(profit),
        "orders": int(orders),
        "aov": float(revenue / orders) if orders else 0.0,
        "margin": float(profit / revenue * 100) if revenue else 0.0,
    }


def pct_change(new, old):
    return None if not old else round((new - old) / old * 100, 1)


def group_sum(df, col, top=None):
    grouped = (
        df.groupby(col)[["revenue", "profit"]]
        .sum()
        .sort_values("revenue", ascending=False)
    )

    if top:
        grouped = grouped.head(top)

    return {
        "labels": grouped.index.tolist(),
        "revenue": grouped["revenue"].round(2).tolist(),
        "profit": grouped["profit"].round(2).tolist(),
    }


# ------------------------------------------------------------
# PAGES
# ------------------------------------------------------------

@app.before_request
def require_login():
    """Everything except the login page and static files needs a session."""
    if request.endpoint in ("login", "static") or session.get("user"):
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required"}), 401

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if username == ADMIN_USER and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["user"] = username
            return redirect(url_for("index"))

        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"))


# ------------------------------------------------------------
# API: FILTERS
# ------------------------------------------------------------

@app.route("/api/filters")
def api_filters():
    return jsonify({
        "regions": sorted(DF["region"].dropna().unique().tolist()),
        "categories": sorted(DF["category"].dropna().unique().tolist()),
        "min_date": MIN_DATE.strftime("%Y-%m-%d"),
        "max_date": MAX_DATE.strftime("%Y-%m-%d"),
    })


# ------------------------------------------------------------
# API: SUMMARY
# ------------------------------------------------------------

@app.route("/api/summary")
def api_summary():
    start, end = get_range()

    current = totals(subset(start, end))

    span = end - start
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - span

    previous = totals(subset(prev_start, prev_end))

    kpis = {
        key: {
            "value": value,
            "change": pct_change(value, previous[key]),
        }
        for key, value in current.items()
    }

    return jsonify(kpis)


# ------------------------------------------------------------
# API: TREND AND FORECAST
# ------------------------------------------------------------

@app.route("/api/trend")
def api_trend():
    start, end = get_range()
    df = subset(start, end)

    gran = request.args.get("granularity", "month")

    rule, fmt = {
        "month": ("MS", "%b %Y"),
        "week": ("W", "%d %b %y"),
        "day": ("D", "%d %b"),
    }.get(gran, ("MS", "%b %Y"))

    if df.empty:
        return jsonify({
            "labels": [],
            "revenue": [],
            "profit": [],
            "forecast": [],
        })

    grouped = (
        df.set_index("date")[["revenue", "profit"]]
        .resample(rule)
        .sum()
    )

    labels = [date.strftime(fmt) for date in grouped.index]
    revenue = grouped["revenue"].round(2).tolist()
    profit = grouped["profit"].round(2).tolist()

    forecast = [None] * len(labels)

    if gran == "month" and len(grouped) >= 4:
        values = grouped["revenue"].to_numpy()
        x = np.arange(len(values))

        slope, intercept = np.polyfit(x, values, 1)

        future_dates = pd.date_range(
            grouped.index[-1] + pd.DateOffset(months=1),
            periods=3,
            freq="MS",
        )

        future_values = [
            round(float(slope * (len(values) + i) + intercept), 2)
            for i in range(3)
        ]

        forecast[-1] = revenue[-1]

        labels += [date.strftime(fmt) for date in future_dates]
        forecast += future_values

        revenue += [None] * 3
        profit += [None] * 3

    return jsonify({
        "labels": labels,
        "revenue": revenue,
        "profit": profit,
        "forecast": forecast,
    })


# ------------------------------------------------------------
# API: BREAKDOWN
# ------------------------------------------------------------

@app.route("/api/breakdown")
def api_breakdown():
    start, end = get_range()
    df = subset(start, end)

    return jsonify({
        "category": group_sum(df, "category"),
        "region": group_sum(df, "region"),
        "channel": group_sum(df, "channel"),
        "segment": group_sum(df, "segment"),
        "products": group_sum(df, "product", top=8),
    })


# ------------------------------------------------------------
# API: INSIGHTS
# ------------------------------------------------------------

@app.route("/api/insights")
def api_insights():
    start, end = get_range()
    df = subset(start, end)

    if df.empty:
        return jsonify(["No orders match the current filters."])

    output = []

    top_region = df.groupby("region")["revenue"].sum().idxmax()
    top_category = df.groupby("category")["profit"].sum().idxmax()
    top_product = df.groupby("product")["revenue"].sum().idxmax()

    monthly = df.set_index("date")["revenue"].resample("MS").sum()
    best_month = monthly.idxmax().strftime("%B %Y")

    margins = df.groupby("category").apply(
        lambda group: (
            group["profit"].sum() / group["revenue"].sum() * 100
            if group["revenue"].sum()
            else 0
        ),
        include_groups=False,
    )

    discounted_share = (df["discount"] > 0).mean() * 100

    output.append(
        f"{top_region} is your strongest region by revenue."
    )
    output.append(
        f"{top_category} earns the most profit of any category."
    )
    output.append(
        f"{top_product} is the top-selling product by revenue."
    )
    output.append(
        f"{best_month} was the best month, with "
        f"{format_inr(monthly.max())} in revenue."
    )

    if not margins.empty:
        output.append(
            f"{margins.idxmax()} has the highest margin at "
            f"{margins.max():.1f}%; "
            f"{margins.idxmin()} has the lowest at "
            f"{margins.min():.1f}%."
        )

    output.append(
        f"{discounted_share:.0f}% of orders used a discount."
    )

    return jsonify(output)


# ------------------------------------------------------------
# API: ORDERS
# ------------------------------------------------------------

@app.route("/api/orders")
def api_orders():
    start, end = get_range()
    df = subset(start, end)

    query = (request.args.get("q") or "").strip().lower()

    if query:
        mask = (
            df["order_id"].astype(str).str.lower().str.contains(
                query, regex=False
            )
            | df["product"].astype(str).str.lower().str.contains(
                query, regex=False
            )
            | df["category"].astype(str).str.lower().str.contains(
                query, regex=False
            )
            | df["region"].astype(str).str.lower().str.contains(
                query, regex=False
            )
        )

        df = df[mask]

    sort = request.args.get("sort", "date")

    if sort not in df.columns:
        sort = "date"

    ascending = request.args.get("dir", "desc") == "asc"

    df = df.sort_values(sort, ascending=ascending)

    page = max(int(request.args.get("page", 1)), 1)
    per_page = 10
    total = len(df)

    rows = df.iloc[(page - 1) * per_page:page * per_page].copy()

    rows["date"] = rows["date"].dt.strftime("%Y-%m-%d")

    columns = [
        "order_id",
        "date",
        "region",
        "category",
        "product",
        "quantity",
        "revenue",
        "profit",
    ]

    return jsonify({
        "rows": rows[columns].to_dict("records"),
        "total": total,
        "page": page,
        "pages": max(-(-total // per_page), 1),
    })


# ------------------------------------------------------------
# API: EXPORT
# ------------------------------------------------------------

@app.route("/api/export")
def api_export():
    start, end = get_range()

    csv_data = subset(start, end).to_csv(index=False)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=sales_export.csv"
        },
    )


# ------------------------------------------------------------
# START FLASK
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)