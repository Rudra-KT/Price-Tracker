# tracker.py
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from flask import Flask

from database import get_products, get_last_price, insert_price, update_last_notified, get_db_connection
from notifier import send_email
import logging
import re
# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.110 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def should_send_notification(product):
    """Check if an email notification should be sent."""
    last_notified = product.get('last_notified')  # Fetch from the database
    print("LAST NOTIFIED",last_notified)
    if last_notified:
        # Allow notifications if it's been more than 24 hours since the last one
        return datetime.now() > last_notified + timedelta(days=1)
    return True  # Send if no previous notification exists

def scrape_price_amazon(url):
    """Scrape price from the Amazon product page, following redirects if necessary."""
    try:
        logging.debug(f"Fetching Amazon URL: {url}")
        session = requests.Session()  # Use a session to handle redirects
        response = session.get(url, headers=HEADERS, allow_redirects=True)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for Amazon price element
        price_element = soup.select_one("span.a-price-whole")
        if price_element:
            price = price_element.text.replace(",", "").strip()
            print(f"Extracted raw price text for : {price}")
            return float(price)
        else:
            logging.error("Error: Price element not found on Amazon.")
            return None
    except Exception as e:
        logging.error(f"Amazon scraping failed: {e}")
        return None


def scrape_price_flipkart(url):
    """Scrape price from the Flipkart product page."""
    try:
        print(f"Fetching Flipkart URL: {url}")
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for Flipkart price element
        price_element = soup.select_one("div.Nx9bqj.CxhGGd")
        if price_element:
            price = price_element.text.replace("₹", "").replace(",", "").strip()
            print(f"Extracted raw price text : {price}")
            return float(price)
        else:
            logging.error("Error: Price element not found on Flipkart.")
            return None
    except Exception as e:
        logging.error(f"Flipkart scraping failed: {e}")
        return None


def scrape_price(url):
    """Determine whether the product is from Amazon or Flipkart and scrape price."""
    if "amazon" in url or "amzn" in url:  # Handle both full and shortened Amazon URLs
        return scrape_price_amazon(url)
    elif "flipkart" in url:
        return scrape_price_flipkart(url)
    else:
        logging.error(f"Unsupported website for URL: {url}")
        return None

def get_asin(url):#for amazon
    # Follow the short URL redirection
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the product page
        soup = BeautifulSoup(response.content, 'html.parser')
        # Locate the ASIN in the product page's metadata
        asin = soup.find('input', {'id': 'ASIN'})['value']
        return asin
    return None

def extract_product_id(url): #for flipkart
    try:
        # Follow the redirect to get the final URL
        response = requests.get(url)
        final_url = response.url  # This is the full URL after redirection

        # Now extract the product ID from the final URL
        match = re.search(r'/p/([^/?]+)', final_url)
        if match:
            return match.group(1)  # Returns the product ID
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")

    return None  # Returns None if no match is found or an error occurs

def track_prices():
    """Track prices for all products."""
    products = get_products()  # Fetch products from DB
    for product in products:
        logging.info(f"Tracking product: {product['product_name']} ({product['product_url']})")

        current_price = scrape_price(product['product_url'])

        if current_price is not None:
            last_price = get_last_price(product['product_type'])
            last_emailed_price = product.get('last_emailed_price', float('inf'))  # Default to infinity

            insert_price(current_price, product['product_type'])
            logging.info(f"Current price of {product['product_name']}: {current_price} \nLast tracked price of {product['product_name']}: {last_price}")

            if current_price < product['desired_price']:
                if should_send_notification(product) or current_price < last_emailed_price :
                    # Send notification only if the current price is lower than the last emailed price
                    print("CURRENT PRICE ",current_price)
                    print("LAST MAILED PRICE ", last_emailed_price)
                    if current_price < last_emailed_price:
                        #logging.info(f"Sending notification for product: {product['product_name']} - Price dropped to ₹{current_price}")
                        print(f"Sending notification for product: {product['product_name']} - Price dropped to ₹{current_price}")
                        send_email(
                            product['email'],
                            f"Price Drop Alert 🤑‼️ for {product['product_name']} ✨",
                            f"The price of your registered product has dropped to ₹{current_price}. \nCheck it out right now 👇 ! \n{product['product_url']}"
                        )
                        # Update the last notified timestamp and last emailed price in the database
                        update_last_notified(product['product_type'], current_price)
                    else:
                        #logging.info("Current price is not lower than the last emailed price. Notification not sent to avoid spamming.")
                        print("Current price is not lower than the last emailed price. Notification not sent to avoid spamming.")
                else:
                    #logging.info("Notification not sent due to time constraints.")
                    print("Notification not sent due to time constraints.")
        else:
            logging.warning(f"Failed to retrieve price for {product['product_name']}")