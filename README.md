# 📈 PriceTracker

![Project Status](https://img.shields.io/badge/status-inactive-brightgreen.svg)
![Python](https://img.shields.io/badge/python-v3.10+-blue)


**A web-based price tracking application** to monitor product prices on e-commerce sites like Amazon and Flipkart. This app helps users set target prices, and notifies them when the desired price is reached.

---

## 🚀 Features
- **User Authentication:** Login, registration, and account management features.
- **Price Tracking:** Monitor product prices from multiple sources.
- **Alerts/Notifications:** Get email notifications when a product drops below your desired price.
- **Product History:** View historical price changes.
- **Responsive UI:** Frontend built with HTML, CSS, and JavaScript for a smooth user experience.

---

## 📂 Project Structure
# PriceTracker

## Project Structure

```plaintext
priceTracker_2/
│
├── .venv/                # Virtual environment folder
│   ├── Lib/
│   └── Scripts/
│
├── static/               # Static assets (CSS, JavaScript)
│   ├── css/              # CSS files
│   │   ├── dashboard.css
│   │   ├── home.css
│   │   ├── login.css
│   │   ├── product_history.css
│   │   ├── register.css
│   │   └── unregister.css
│   └── js/               # JavaScript files
│       ├── login.js
│       └── register.js
│
├── templates/            # HTML templates
│   ├── dashboard.html
│   ├── home.html
│   ├── login.html
│   ├── product_history.html
│   ├── register.html
│   └── unregister.html
│
├── .gitignore            # Git ignore file
├── app.py                # Main Flask app
├── credentials.json      # Email credentials for notifications
├── database.py           # Database connection and queries
├── notifier.py           # Email notification service
├── requirements.txt      # Python dependencies
└── tracker.py            # Price tracking logic
```

---

## 🛠️ Technologies Used
- **Backend:** Python (Flask Framework)
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** MySQL
- **Web Scraping:** `requests` library
- **Email Notifications:** `smtplib`
- **Version Control:** Git

---

## 🔧 Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Rudra-KT/Price-Tracker.git
   cd Price-Tracker
   
## Create a virtual environment:
```
python -m venv .venv
source .venv/bin/activate  # For Linux/macOS
.venv\Scripts\activate     # For Windows
```
## Install dependencies:
``
pip install -r requirements.txt
``

## Set up the MySQL database and tables 



📬 Notifications Setup
```
Add your email credentials in credentials.json:
{
  "email": "your-email@example.com",
  "password": "your-email-password"
}
```
- **Ensure that less secure apps are enabled for the email provider (e.g., Gmail)**

## 💡 Usage Instructions

1. Register a new account or log in.
2. Add products by providing their URLs and desired prices.
3. Track the prices periodically via the dashboard.
4. Get notifications when a product's price drops below your target.

## 🐛 Known Issues

- **Blocked scraping requests:** Some e-commerce websites may block scraping. Use a proxy server if needed.
- **Captcha on Amazon:** Implement headless browser solutions if frequent captchas are encountered.
