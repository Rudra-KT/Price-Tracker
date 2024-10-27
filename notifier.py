import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def send_email(to_email, subject, body):
    """Send an email to the user."""
    try:
        # Load email credentials from environment variables
        from_email = os.getenv('EMAIL')
        password = os.getenv('EMAIL_PASSWORD')

        if not from_email or not password:
            raise ValueError("Email credentials are missing. Please check your environment variables.")

        # Prepare email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        logging.info(f"Preparing to send email to {to_email}")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        logging.info(f"{subject} email alert successfully sent to {to_email}!")
        server.quit()

    except Exception as e:
        logging.error(f"Failed to send email: {e}")
