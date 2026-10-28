# 📊 Sales Data Analysis Dashboard & Business Intelligence Web Application

An interactive web-based analytics dashboard designed to analyze sales performance, monitor key business metrics, visualize trends, and generate data-driven insights.

Built using Python, Flask, MySQL, Pandas, NumPy, HTML, CSS, and JavaScript, this project combines data analysis with interactive visualizations to make sales data easier to understand.

## 🚀 Features

* **Interactive KPI Dashboard:** Monitor revenue, profit, total orders, average order value, and profit margin.
* **Dynamic Data Filtering:** Filter sales records by date range, region, and product category.
* **Sales Trend Analysis:** Visualize daily, weekly, and monthly revenue and profit trends.
* **Revenue Forecasting:** Generate a basic three-month revenue forecast using linear regression.
* **Business Intelligence:** Identify top-performing regions, categories, products, and sales periods.
* **Interactive Visualizations:** Explore sales performance through charts and graphs.
* **Order Management View:** Search, sort, and navigate through sales records using a paginated table.
* **CSV Export:** Export filtered sales data for further analysis.
* **Login Authentication:** Protect dashboard pages and API endpoints with session-based authentication.
* **Customizable Interface:** Switch between dark and light themes.

## 🛠️ Technologies Used

| Technology | Purpose                                 |
| ---------- | --------------------------------------- |
| Python     | Backend programming and data processing |
| Flask      | Web application and API development     |
| MySQL      | Sales data storage                      |
| Pandas     | Data manipulation and analysis          |
| NumPy      | Numerical computation and forecasting   |
| HTML5      | Web page structure                      |
| CSS3       | Styling and responsive interface        |
| JavaScript | Interactive dashboard functionality     |
| Chart.js   | Data visualization                      |

## ⚙️ Installation and Setup

### Prerequisites

* Python 3.10 or a compatible version
* MySQL Server
* Visual Studio Code or another code editor

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd sales_dashboard111245
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure MySQL

Create the database in MySQL:

```sql
CREATE DATABASE sales_dashboard;
```

Update the database connection settings in `app.py` to match your MySQL username and password.

**Security note:** Configure database credentials and application secrets through environment variables rather than committing real passwords to GitHub.

### Step 5: Run the Application

```bash
python app.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

Sign in using the credentials configured for your application.

## 📂 Project Structure

```text
sales_dashboard111245/
│
├── app.py
├── data_generator.py
├── requirements.txt
├── README.md
│
├── data/
│   └── sales_data.csv
│
├── templates/
│   ├── index.html
│   └── login.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── dashboard.js
```

## 📈 Key Analytical Capabilities

The dashboard provides insights into:

* Revenue and profit performance over time.
* Sales distribution across regions and categories.
* Product and sales-channel performance.
* Average order value and profit margins.
* Comparisons with previous periods.
* Estimated revenue trends for upcoming months.

## 🎯 Project Objective

The objective of this project is to demonstrate how data analytics, database management, and web development can be combined to create a practical Business Intelligence application.

It provides a centralized interface for exploring sales data and supports better understanding of business performance through interactive visualizations and analytical insights.

## 🔮 Future Enhancements

* Upload custom sales datasets through the dashboard.
* Add advanced forecasting models.
* Implement multiple user accounts and role-based access.
* Support additional filters and downloadable analytical reports.
* Deploy the application to a cloud platform.

## 👨‍💻 Author

Developed as an academic project to apply concepts of data analysis, database management, and full-stack web development.
