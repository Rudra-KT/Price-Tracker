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

## 🗃️ Database Setup

To set up the MySQL database and tables for this project, follow these steps:

1. Open your MySQL client or command-line interface.
2. Connect to your MySQL server.
3. Run the following SQL commands:

```sql
-- Drop existing tables if they exist
DROP TABLE IF EXISTS `password_reset_attempts`;
DROP TABLE IF EXISTS `password_resets`;
DROP TABLE IF EXISTS `price_history`;
DROP TABLE IF EXISTS `user_products`;
DROP TABLE IF EXISTS `users`;

-- Create users table
CREATE TABLE `users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create user_products table
CREATE TABLE `user_products` (
  `product_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `product_name` VARCHAR(255) NOT NULL,
  `product_url` TEXT NOT NULL,
  `desired_price` DECIMAL(10,2) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `product_type` INT NOT NULL DEFAULT '0',
  `asin` VARCHAR(16) DEFAULT NULL,
  `last_notified` DATETIME DEFAULT NULL,
  `last_emailed_price` DECIMAL(10,2) DEFAULT NULL,
  PRIMARY KEY (`product_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_products_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create price_history table
CREATE TABLE `price_history` (
  `history_id` INT NOT NULL AUTO_INCREMENT,
  `recorded_price` DECIMAL(10,2) NOT NULL,
  `recorded_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `product_type` INT NOT NULL,
  PRIMARY KEY (`history_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create password_resets table
CREATE TABLE `password_resets` (
  `reset_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  `used` TINYINT(1) DEFAULT '0',
  `used_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`reset_id`),
  KEY `user_id` (`user_id`),
  KEY `idx_token` (`token`),
  CONSTRAINT `password_resets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create password_reset_attempts table
CREATE TABLE `password_reset_attempts` (
  `attempt_id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL,
  `attempt_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`attempt_id`),
  KEY `idx_email_time` (`email`, `attempt_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

```

## 📬 Notifications Setup
```
Add your email credentials in credentials.json:
{
  "email": "your-email@example.com",
  "password": "your-email-password"
}
```
- **Ensure that less secure apps are enabled for the email provider (e.g., Gmail)** otherwise you wont be able to send mails to users .

## 💡 Usage Instructions

1. Register a new account or log in.
2. Add products by providing their URLs and desired prices.
3. Track the prices periodically via the dashboard.
4. Get notifications when a product's price drops below your target.

## 🐛 Known Issues

- **Blocked scraping requests:** Some e-commerce websites may block scraping (in particular when deploying via pythonanywhere) . Use a proxy server if needed (didnt try a paid proxy , free proxies didnt work in my case tho 😥). (altho it works perfectly on local deployment)
  
- **Captcha on Amazon:** Implement headless browser solutions if frequent captchas are encountered. (using selenium) (this too didnt work for me when i deployed through pythonanywhere 😥)
