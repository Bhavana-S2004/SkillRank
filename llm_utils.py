import openai
import os

# Set your OpenAI API key from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_sql_query(nl_question):
    """Generates a SQL query from a natural language question using an LLM."""
    
    # Define the database schema for the LLM's context
    SCHEMA = """
    CREATE TABLE customers (id INTEGER, name TEXT, email TEXT, city TEXT, signup_date TEXT);
    CREATE TABLE products (id TEXT, name TEXT, category TEXT, price REAL, stock INTEGER);
    CREATE TABLE orders (id TEXT, customer_id TEXT, product_id TEXT, quantity INTEGER, order_date TEXT, total REAL);
    CREATE TABLE sales (id INTEGER, order_id TEXT, revenue REAL, profit_margin REAL, sales_date TEXT);
    """
    
    prompt = f"Given the following SQLite database schema:\n{SCHEMA}\n\nConvert the following natural language question into a valid SQL query. Be precise and use the correct column names from the schema. If the question involves dates, use the format 'YYYY-MM-DD'. If a column name has a space, surround it with double quotes. For example, 'Total Amount' should be \"Total Amount\".\n\nQuestion: {nl_question}\nSQL:"

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can use a different model if you prefer
            prompt=prompt,
            max_tokens=256,
            stop=["\n\n"]
        )
        sql_query = response.choices[0].text.strip()
        return sql_query
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None