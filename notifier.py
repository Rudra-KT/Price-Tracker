import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_credentials():
    """Load email credentials from credentials.json."""
    try:
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)
        return credentials
    except Exception as e:
        logging.error(f"Failed to load credentials: {e}")
        raise

def send_email(to_email, subject, body):
    """Send an email to the user when the price drops."""
    try:
        # Load credentials
        credentials = load_credentials()
        from_email = credentials['email']
        password = credentials['password']

        # Prepare email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        print(f"Preparing to send email to {to_email}")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        print(f"Price Drop email alert successfully sent to {to_email}!")
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
