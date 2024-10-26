from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import MySQLdb.cursors
import threading
import time

from notifier import send_email
from tracker import track_prices, scrape_price, get_asin, extract_product_id
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
    email = ""  # Initialize email as an empty string
    session.pop('error', None)

    if request.method == 'POST':
        email = request.form['email']

        # Check if the email already exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            # If user exists, set an error message in the session
            session['error'] = "User already exists. Please log in."
            cursor.close()  # Close cursor
            return render_template('register.html', error=session['error'], email=email)

        password = request.form['password']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert the new user into the database
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (%s, %s)', (email, password_hash))
        mysql.connection.commit()
        cursor.close()  # Close cursor

        # Send registration confirmation email
        email_subject = "THANKS FOR REGISTERING ON PRICE TRACKER 😎‼️"
        email_body = (
            f"Your account has been successfully created. "
            f"You will receive a mail when your registered products prices drop below your desired prices 😼\n\n"
            f"Account Details:\n"
            f"Email: {email}\n"
            f"Password: {password}\n"
            f"Date of Registration: {created_at}\n"
        )
        send_email(email, email_subject, email_body)

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    # Clear the error message from the session after rendering
    error = session.pop('error', None)
    return render_template('register.html', error=error, email=email)

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
            session['user_email'] = user['email']  # Store the user's email in the session
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
    desired_price = Decimal(request.form['desired_price'])

    if "amazon" in product_url or "amzn" in product_url:
        product_asin = get_asin(product_url)
    elif "flipkart" in product_url or 'fkrt.it' in product_url:
        product_asin = extract_product_id(product_url)
    else:
        flash('Only Amazon or Flipkart links supported atm', 'error')
        return redirect(url_for('dashboard'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the product URL already exists for the current user
    cursor.execute(
        'SELECT * FROM user_products WHERE asin = %s AND user_id = %s',
        (product_asin, current_user.id)
    )
    existing_product = cursor.fetchone()

    if existing_product:
        flash('You have already added this product to your list.', 'info')
    else:
        cursor.execute(
            'SELECT * FROM user_products WHERE asin = %s',
            (product_asin,)
        )
        existing_product = cursor.fetchone()
        if existing_product :
            product_type = existing_product['product_type']
            cursor.execute(
                'INSERT INTO user_products (user_id, product_name, product_url, desired_price, product_type, asin) VALUES (%s, %s, %s, %s, %s, %s)',
                (current_user.id, product_name, product_url, desired_price, product_type, product_asin)
            )
            mysql.connection.commit()
            current_price = scrape_price(product_url)
            # Save the price history
            cursor.execute(
                'INSERT INTO price_history (recorded_price, product_type) VALUES (%s, %s)',
                (current_price, product_type)
            )
            mysql.connection.commit()
            flash('Product added successfully!', 'success')

        else:
            # Generate a new product_type value
            cursor.execute('SELECT COALESCE(MAX(product_type), 0) + 1 AS new_product_type FROM user_products')
            product_type = cursor.fetchone()['new_product_type']
            cursor.execute(
                'INSERT INTO user_products (user_id, product_name, product_url, desired_price, product_type, asin) VALUES (%s, %s, %s, %s, %s, %s)',
                (current_user.id, product_name, product_url, desired_price, product_type, product_asin)
            )
            mysql.connection.commit()

            current_price = scrape_price(product_url)
            # Save the price history
            cursor.execute(
                'INSERT INTO price_history (recorded_price, product_type) VALUES (%s, %s)',
                (current_price, product_type)
            )
            mysql.connection.commit()
            flash('Product added successfully!', 'success')

    cursor.close()
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
    product_type = request.args.get('product_type')

    if not product_type:
        return "Product type is required", 400

    # Fetch price history from the database
    price_history = get_price_history(product_type)

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
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT email FROM users WHERE user_id = %s',
            (current_user.id,)
        )
        result = cursor.fetchone()
        if result:
            email = result['email']  # Get the current user's email
        else:
            return render_template('unregister.html',console_log = 'Unable to find your account')

        deletion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Capture the current date and time

        delete_user(current_user.id)  # Delete the current user's records
        logout_user()  # Log out the user after unregistration

        # Email content with formatted deletion date and time
        email_subject = "Account Deletion Confirmation"
        email_body = (
            f"Your account has been successfully deleted.\nSad to see you leaving us 😢😢\n"
            f"Account Details:\n"
            f"Email: {email}\n"
            f"Date of Deletion: {deletion_time}\n"
        )

        # Send account deletion confirmation email
        send_email(email, email_subject, email_body)

        return redirect(url_for('unregister'))  # Redirect to the unregister page to show the message

    return render_template('unregister.html')  # Render the confirmation template

@app.route('/change-password', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        # Get the currently logged-in user's email from session
        user_email = session.get('user_email')

        if not user_email:
            flash('You need to be logged in to change your password.', 'error')
            return redirect(url_for('login'))  # Redirect to login if not logged in

        # Check the current password
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT password_hash FROM users WHERE email = %s ', (user_email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password_hash'], current_password):
            if new_password == confirm_new_password:
                # Hash the new password and update it in the database
                new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                cursor.execute('UPDATE users SET password_hash = %s WHERE email = %s', (new_password_hash, user_email))
                mysql.connection.commit()

                # Capture the current date and time
                change_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Email content with formatted change date and time
                email_subject = "Password Change Notification"
                email_body = (
                    f"Your password has been changed successfully ✅ .\n\n"
                    f"Account Details:\n"
                    f"Email: {user_email}\n"
                    f"Date of Change: {change_time}\n"
                )

                # Send password change notification email
                send_email(user_email, email_subject, email_body)

                flash('Your password has been changed successfully!', 'success')
                return render_template('change_password.html')  # Render the same template with the success message
            else:
                flash('New passwords do not match. Please try again.', 'error')
        else:
            flash('Current password is incorrect. Please try again.', 'error')

    return render_template('change_password.html')


if __name__ == '__main__':
    # Start price tracker thread
    tracker_thread = threading.Thread(target=start_price_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()

    logging.info("Starting Flask application")
    app.run(debug=True)