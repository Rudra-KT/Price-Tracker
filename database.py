import MySQLdb
from flask import current_app as app
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Connect to MySQL database."""
    logging.debug("Establishing database connection")
    try:
        connection = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=MySQLdb.cursors.DictCursor
        )
        logging.debug("Database connection established successfully")
        return connection
    except MySQLdb.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

def get_products():
    """Fetch all products for price tracking."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.email, p.product_id, p.product_name, p.product_url, p.desired_price 
            FROM users u JOIN user_products p ON u.user_id = p.user_id
        """)
        products = cursor.fetchall()
        logging.debug(f"Fetched products: {products}")
        return products
    except MySQLdb.Error as e:
        logging.error(f"Error fetching products: {e}")
        return []
    finally:
        conn.close()

def get_last_price(product_id):
    """Get the last recorded price for a product."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT recorded_price FROM price_history WHERE product_id = %s ORDER BY recorded_at DESC LIMIT 1", (product_id,))
        result = cursor.fetchone()
        logging.debug(f"Last recorded price for product {product_id}: {result}")
        return result['recorded_price'] if result else None
    except MySQLdb.Error as e:
        logging.error(f"Error fetching last price for product {product_id}: {e}")
        return None
    finally:
        conn.close()

def insert_price(product_id, price):
    """Insert new price into price history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO price_history (product_id, recorded_price) VALUES (%s, %s)", (product_id, price))
        conn.commit()
        logging.debug(f"Inserted price {price} for product {product_id}")
    except MySQLdb.Error as e:
        logging.error(f"Error inserting price for product {product_id}: {e}")
    finally:
        conn.close()

def get_price_history(product_id):
    """Fetch price history for a specific product."""
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionary-like results
    try:
        # Query to get the price history for the specified product_id
        query = "SELECT recorded_price, recorded_at FROM price_history WHERE product_id = %s ORDER BY recorded_at DESC"
        cursor.execute(query, (product_id,))

        # Fetch all the results
        price_history = cursor.fetchall()

        return price_history  # Return the list of price history records

    except MySQLdb.Error as err:
        logging.error(f"Error fetching price history: {err}")
        return []

    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()


def delete_user(user_id):
    """Delete user and their associated products from the database."""
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    # Delete associated products first to maintain referential integrity
    cursor.execute('DELETE FROM user_products WHERE user_id = %s', (user_id,))
    # Now delete the user
    cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
    conn.commit()
