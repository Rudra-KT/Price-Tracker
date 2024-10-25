from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import MySQLdb.cursors
import threading
import time
from tracker import track_prices
import logging
from database import get_price_history, delete_user
from decimal import Decimal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 's@20040604'
app.config['MYSQL_DB'] = 'price_tracker_users'

mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user['user_id'])
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (%s, %s)', (email, password_hash))
        mysql.connection.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            login_user(User(user['user_id']))
            return redirect(url_for('dashboard'))
        else:
            flash('Email or password is incorrect. Please try again.', 'danger')
            return redirect(url_for('login'))  # Redirect to the login page to avoid resubmission

    return render_template('login.html')



def shorten_url(url):
    """Shorten the URL for display purposes."""
    if len(url) > 30:  # Example threshold for shortening
        return url[:15] + '...' + url[-12:]  # Shorten URL to 15...12
    return url

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user_products WHERE user_id = %s', (current_user.id,))
    products = cursor.fetchall()
    for product in products:
        product['shortened_url'] = shorten_url(product['product_url'])
    return render_template('dashboard.html', products=products)

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    product_name = request.form['product_name']
    product_url = request.form['product_url']
    desired_price = request.form['desired_price']

    cursor = mysql.connection.cursor()
    cursor.execute(
        'INSERT INTO user_products (user_id, product_name, product_url, desired_price) VALUES (%s, %s, %s, %s)',
        (current_user.id, product_name, product_url, desired_price))
    mysql.connection.commit()
    return redirect(url_for('dashboard'))

@app.route('/unregister_product/<int:product_id>', methods=['POST'])
@login_required
def unregister_product(product_id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM user_products WHERE product_id = %s AND user_id = %s',
                   (product_id, current_user.id))
    mysql.connection.commit()
    return redirect(url_for('dashboard'))

def update_desired_price(product_id, new_price):
    """Update the desired price for a given product."""
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE user_products SET desired_price = %s WHERE product_id = %s", (new_price, product_id))
    mysql.connection.commit()

@app.route('/update_price/<int:product_id>', methods=['POST'])
@login_required
def update_price(product_id):
    new_price = request.form['desired_price']
    update_desired_price(product_id, new_price)
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


def start_price_tracker():
    with app.app_context():  # Push the application context
        logging.info("Price tracker thread started.")
        sleep_time = 6*3600
        while True:
            try:
                track_prices()  # Now inside the app context
                logging.info("Price tracking executed successfully.")
            except Exception as e:
                logging.error(f"Error while tracking prices: {e}")

            logging.info(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)  # Check every 6 hours
            logging.info("Woke up, tracking prices again.")


def serialize_price_history(history):
    """Convert Decimal and datetime objects to JSON-serializable types."""
    return [
        {
            'price': float(entry['recorded_price']) if isinstance(entry['recorded_price'], Decimal) else entry['recorded_price'],
            'timestamp': entry['recorded_at'].isoformat()  # Convert datetime to ISO string
        }
        for entry in history
    ]

@app.route('/product_history', methods=['GET'])
@login_required
def view_price_history():
    product_id = request.args.get('productId')

    if not product_id:
        return "Product ID is required", 400

    # Fetch price history from the database
    price_history = get_price_history(product_id)

    if not price_history:
        return "No price history found for this product.", 404

    # Serialize price history for JSON
    serialized_history = serialize_price_history(price_history)

    # Render the template with price history data
    return render_template('product_history.html', price_history=serialized_history)

@app.route('/unregister', methods=['GET', 'POST'])
@login_required
def unregister():
    if request.method == 'POST':
        delete_user(current_user.id)  # Delete the current user's records
        logout_user()  # Log out the user after unregistration
        return redirect(url_for('unregister'))  # Redirect to the unregister page to show the message

    return render_template('unregister.html')  # Render the confirmation template

if __name__ == '__main__':
    # Start price tracker thread
    tracker_thread = threading.Thread(target=start_price_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()

    logging.info("Starting Flask application")
    app.run(debug=True)