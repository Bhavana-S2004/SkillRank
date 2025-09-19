import sqlite3

def execute_query(sql_query):
    """Connects to the database and executes a given SQL query."""
    try:
        conn = sqlite3.connect('business_dashboard.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Database query failed: {e}")
        return None