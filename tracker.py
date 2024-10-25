import requests
from bs4 import BeautifulSoup
from database import get_products, get_last_price, insert_price
from notifier import send_email
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.110 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}


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
            print(f"Extracted raw price text: {price}")
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


def track_prices():
    """Track prices for all products."""
    products = get_products()  # Fetch products from DB
    for product in products:
        print(f"Tracking product: {product['product_name']} ({product['product_url']})")
        current_price = scrape_price(product['product_url'])
        if current_price:
            last_price = get_last_price(product['product_id'])
            insert_price(product['product_id'], current_price)
            print(f"Current price: {current_price}, Last price: {last_price}")

            if current_price < product['desired_price'] and (last_price is None or current_price < last_price):
                print(
                    f"Sending notification for product: {product['product_name']} - Price dropped to ₹{current_price}")
                send_email(
                    product['email'],
                    f"Price Drop Alert 🤑‼️ for {product['product_name']} ✨",
                    f"The price of your registered product has dropped to ₹{current_price}. \nCheck it out right now 👇 ! \n{product['product_url']}  "
                )
        else:
            print(f"Failed to retrieve price for {product['product_name']}")
