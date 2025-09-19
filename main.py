import pandas as pd
import sqlite3
import zipfile
import os

# --- Step 1: Extract the zip files ---
# This part is fine; it correctly extracts the files to dedicated folders.

def extract_zip(file_path, output_dir):
    """Extracts all contents of a zip file to a specified directory."""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            os.makedirs(output_dir, exist_ok=True)
            zip_ref.extractall(output_dir)
            print(f"Successfully extracted {file_path} to {output_dir}/")
    except zipfile.BadZipFile:
        print(f"Error: {file_path} is not a valid zip file.")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")

zip_files_and_dirs = {
    'data1.zip': 'data1',
    'data2.zip': 'data2',
    'data3.zip': 'data3'
}

for zip_file, output_dir in zip_files_and_dirs.items():
    extract_zip(zip_file, output_dir)

# --- Step 2: Load and Preprocess Data ---

try:
    ecommerce_raw = pd.read_csv('data1/data.csv', encoding='latin-1')
    retail_raw = pd.read_csv('data2/retail_sales_dataset.csv', encoding='latin-1')
    customers_raw = pd.read_csv('data3/ifood_df.csv', encoding='latin-1')
except FileNotFoundError as e:
    print(f"Error loading raw data: {e}. Please ensure the zip files are named correctly and contain the expected CSVs.")
    exit()

# 1. Create the 'customers' DataFrame from ifood_df.csv
customers_df = customers_raw.copy()
# Check for a customer ID column and rename it
if 'ID' in customers_df.columns:
    customers_df = customers_df.rename(columns={'ID': 'id'})
else:
    # If no ID column is found, create one from the index
    customers_df['id'] = customers_df.index + 1

# Rename the date column
if 'Dt_Customer' in customers_df.columns:
    customers_df = customers_df.rename(columns={'Dt_Customer': 'signup_date'})
else:
    customers_df['signup_date'] = None # Add signup_date column if it doesn't exist

# Add placeholder columns if they don't exist
customers_df['name'] = customers_df['id'].apply(lambda x: f"Customer {x}")
customers_df['email'] = customers_df['id'].apply(lambda x: f"customer{x}@example.com")
customers_df['city'] = 'Unknown'

customers_df = customers_df[['id', 'name', 'email', 'city', 'signup_date']].drop_duplicates(subset=['id']).dropna(subset=['id'])


# 2. Consolidate and create 'products', 'orders', and 'sales'
# We will use pandas.merge to handle different column names explicitly
orders_df = pd.DataFrame()

# Process retail data first
if 'Transaction ID' in retail_raw.columns:
    temp_retail = retail_raw.rename(columns={
        'Transaction ID': 'order_id',
        'Customer Gender': 'customer_id',
        'Product Category': 'product_name',
        'Date': 'order_date',
        'Quantity': 'quantity',
        'Total Amount': 'total_amount',
        'Price per Unit': 'unit_price'
    })
    orders_df = pd.concat([orders_df, temp_retail], ignore_index=True)

# Process ecommerce data
if 'InvoiceNo' in ecommerce_raw.columns:
    temp_ecommerce = ecommerce_raw.rename(columns={
        'InvoiceNo': 'order_id',
        'CustomerID': 'customer_id',
        'Description': 'product_name',
        'InvoiceDate': 'order_date',
        'Quantity': 'quantity',
        'UnitPrice': 'unit_price'
    })
    # Calculate total amount for ecommerce data
    temp_ecommerce['total_amount'] = temp_ecommerce['quantity'] * temp_ecommerce['unit_price']
    orders_df = pd.concat([orders_df, temp_ecommerce], ignore_index=True)

# Clean and finalize orders_df
orders_df = orders_df[['order_id', 'customer_id', 'product_name', 'quantity', 'order_date', 'total_amount']].drop_duplicates()
orders_df = orders_df.dropna(subset=['order_id'])

# Generate unique product IDs
# Check if 'unit_price' exists before using it
if 'unit_price' in orders_df.columns:
    products_df = orders_df[['product_name', 'unit_price']].copy().drop_duplicates(subset=['product_name'])
else:
    # If 'unit_price' doesn't exist, create a placeholder or calculate it if possible
    print("Warning: 'unit_price' not found in orders_df. Creating a placeholder.")
    products_df = orders_df[['product_name']].copy().drop_duplicates(subset=['product_name'])
    products_df['unit_price'] = 0  # Placeholder value

products_df['id'] = range(1, len(products_df) + 1)
products_df = products_df.rename(columns={'product_name': 'name', 'unit_price': 'price'})
products_df['category'] = products_df['name']
products_df['stock'] = 0 # Placeholder as stock data is not available

# Merge products_df with orders_df
orders_df = orders_df.merge(products_df[['id', 'name']], left_on='product_name', right_on='name', how='left', suffixes=('_x', '_y'))

# Assign product_id and rename columns
if 'id_y' in orders_df.columns:
    orders_df['product_id'] = orders_df['id_y']
else:
    # Handle the case where 'id_y' does not exist
    print("Error: 'id_y' not found in orders_df. Assigning a default value.")
    orders_df['product_id'] = -1  # Assign a default value

orders_df = orders_df.rename(columns={'order_id': 'id', 'total_amount': 'total'})
# Ensure 'id' is unique before writing to SQL
orders_df['temp_id'] = range(1, len(orders_df) + 1)  # Create a temporary unique ID
orders_df = orders_df[['temp_id', 'customer_id', 'product_id', 'quantity', 'order_date', 'total']].copy()
orders_df = orders_df.rename(columns={'temp_id': 'id'})  # Rename the temporary ID to 'id'


# 3. Create the 'sales' DataFrame from cleaned orders data
sales_df = orders_df.copy()
sales_df = sales_df.rename(columns={
    'id': 'order_id',
    'total': 'revenue',
    'order_date': 'sales_date'
})
sales_df['id'] = range(1, len(sales_df) + 1)
sales_df['profit_margin'] = 0.25
sales_df = sales_df[['id', 'order_id', 'revenue', 'profit_margin', 'sales_date']].drop_duplicates(subset=['id']).dropna(subset=['id'])

# --- Step 3: Load into SQLite Database ---
conn = sqlite3.connect('business_dashboard.db')

customers_df.to_sql('customers', conn, if_exists='replace', index=False)
products_df.to_sql('products', conn, if_exists='replace', index=False)
orders_df.to_sql('orders', conn, if_exists='replace', index=False)
sales_df.to_sql('sales', conn, if_exists='replace', index=False)

conn.commit()
conn.close()

print("Data cleaning and import to SQLite complete!")

#Task 1 successully completed!!!