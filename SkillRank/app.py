from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv
import sqlite3  # Import sqlite3

load_dotenv()

app = Flask(__name__)

# Database setup
DATABASE_URL = 'sqlite:///business_dashboard.db'
engine = create_engine(DATABASE_URL)


def execute_query(sql_query):
    """Executes a SQL query and returns the results as a list of dictionaries."""
    try:
        conn = sqlite3.connect('business_dashboard.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            results.append(dict(zip(column_names, row)))
        conn.close()
        return results
    except Exception as e:
        raise Exception(f"Database error: {e}")


def generate_sql_query(nl_query):
    """Generates a SQL query from a natural language query (without LLM)."""
    nl_query = nl_query.lower()
    if "total sales" in nl_query:
        return "SELECT SUM(revenue) AS total_sales FROM sales"
    elif "top customers" in nl_query:
        return "SELECT c.name, SUM(s.revenue) AS total_revenue FROM customers c JOIN orders o ON c.id = o.customer_id JOIN sales s ON o.id = s.order_id GROUP BY c.name ORDER BY total_revenue DESC LIMIT 5"
    elif "most profitable category" in nl_query:
        return "SELECT p.category, SUM(s.revenue * s.profit_margin) AS total_profit FROM products p JOIN orders o ON p.id = o.product_id JOIN sales s ON o.id = s.order_id GROUP BY p.category ORDER BY total_profit DESC LIMIT 1"
    else:
        return "SELECT * FROM sales LIMIT 10"  # Default query


@app.route('/')
def index():
    """Renders the main dashboard page."""
    # Calculate KPIs here (example)
    with engine.connect() as conn:
        total_sales_query = text("SELECT SUM(revenue) FROM sales")
        total_sales = conn.execute(total_sales_query).scalar()

        total_customers_query = text("SELECT COUNT(*) FROM customers")
        total_customers = conn.execute(total_customers_query).scalar()

        total_orders_query = text("SELECT COUNT(*) FROM orders")
        total_orders = conn.execute(total_orders_query).scalar()

    kpi_data = {
        'total_sales': f"${total_sales:,.2f}",
        'total_customers': total_customers,
        'total_orders': total_orders,
    }

    return render_template('index.html', kpi_data=kpi_data)


@app.route('/query', methods=['POST'])
def query():
    """Handles natural language queries and returns results."""
    nl_query = request.form['query']

    try:
        sql_query = generate_sql_query(nl_query)  # Use keyword-based SQL generator
        results = execute_query(sql_query)  # Execute the SQL query
        return jsonify({'results': results, 'sql': sql_query})  # Return results and SQL
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/chart', methods=['POST'])
def chart():
    """Generates chart data based on a query."""
    nl_query = request.form['query']

    try:
        sql_query = generate_sql_query(nl_query)
        results = execute_query(sql_query)  # get the results
        df = pd.DataFrame(results)  # convert the results to dataframe

        # Basic chart data (customize as needed)
        chart_data = {
            'labels': df.iloc[:, 0].tolist(),  # First column as labels
            'values': df.iloc[:, 1].tolist(),  # Second column as values
            'chart_type': 'bar'  # Default chart type
        }
        return jsonify(chart_data)

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)