# database.py
from datetime import datetime
from flask import current_app as app
import logging
import pymysql
from pymysql.cursors import DictCursor

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Connect to MySQL database."""
    logging.debug("Establishing database connection")
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=DictCursor,
        )
        logging.debug("Database connection established successfully")
        return connection
    except pymysql.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

def get_products():
    """Fetch all products for price tracking."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.email, p.product_id, p.product_name, p.product_url, p.desired_price, p.product_type, p.last_notified, p.last_emailed_price
                FROM users u JOIN user_products p ON u.user_id = p.user_id
            """)
            products = cursor.fetchall()
            logging.debug(f"Fetched products: {products}")
            return products
    except pymysql.Error as e:
        logging.error(f"Error fetching products: {e}")
        return []
    finally:
        conn.close()

def get_last_price(product_type):
    """Get the last recorded price for a product."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT recorded_price FROM price_history WHERE product_type = %s ORDER BY recorded_at DESC LIMIT 1", (product_type,))
            result = cursor.fetchone()
            logging.debug(f"Last recorded price for product type {product_type}: {result}")
            return result['recorded_price'] if result else None
    except pymysql.Error as e:
        logging.error(f"Error fetching last price for product type {product_type}: {e}")
        return None
    finally:
        conn.close()


def insert_price(price, product_type):
    """Insert new price into price history."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO price_history (recorded_price, product_type) VALUES (%s, %s)", (price, product_type))
        conn.commit()
        logging.debug(f"Inserted price {price} for product {product_type}")
    except pymysql.Error as e:
        logging.error(f"Error inserting price for product {product_type}: {e}")
    finally:
        conn.close()

def get_price_history(product_type):
    """Fetch price history for a specific product."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT recorded_price, recorded_at FROM price_history WHERE product_type = %s ORDER BY recorded_at DESC"
            cursor.execute(query, (product_type,))
            price_history = cursor.fetchall()
            return price_history
    except pymysql.Error as err:
        logging.error(f"Error fetching price history: {err}")
        return []
    finally:
        conn.close()

def delete_user(user_id):
    """Delete user and their associated products from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Delete associated products first to maintain referential integrity
            cursor.execute('DELETE FROM user_products WHERE user_id = %s', (user_id,))
            # Now delete the user
            cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
        conn.commit()
    except pymysql.Error as e:
        logging.error(f"Error deleting user {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_last_notified(product_type, current_price):
    """Update the last notified timestamp and last emailed price for a product."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            UPDATE user_products
            SET last_notified = %s, last_emailed_price = %s
            WHERE product_type = %s
            """
            cursor.execute(sql, (datetime.now(), current_price, product_type))
        conn.commit()
    except pymysql.Error as e:
        logging.error(f"Error updating last notified for product type {product_type}: {e}")
        conn.rollback()
    finally:
        conn.close()