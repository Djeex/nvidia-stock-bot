import requests
import logging
import time
import os
import re
from requests.adapters import HTTPAdapter, Retry

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.info("Script started")

# Retrieve environment variables
try:
    DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
    API_URL_SKU = os.environ.get('API_URL_SKU', 'https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia')
    API_URL_STOCK = os.environ.get('API_URL_STOCK', 'https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=')
    REFRESH_TIME = int(os.environ.get('REFRESH_TIME'))
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    PRODUCT_URL = os.environ.get('PRODUCT_URL', 'https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA')
    PRODUCT_NAME = os.environ.get('PRODUCT_NAME')
    
    # Error logging
    if not DISCORD_WEBHOOK_URL:
        logging.error("❌ DISCORD_WEBHOOK_URL is required but not defined.")
        exit(1)

    if not PRODUCT_NAME:
        logging.error("❌ PRODUCT_NAME is required but not defined.")
        exit(1)

    # Regex to extract ID and token
    match = re.search(r'/(\d+)/(.*)', DISCORD_WEBHOOK_URL)
    if match:
        webhook_id = match.group(1)
        webhook_token = match.group(2)

        # Mask last characters of the ID
        masked_webhook_id = webhook_id[:len(webhook_id) - 10] + '*' * 10

        # Mask last characters of the token
        masked_webhook_token = webhook_token[:len(webhook_token) - 120] + '*' * 10

        # Rebuild masked URL
        wh_masked_url = f"https://discord.com/api/webhooks/{masked_webhook_id}/{masked_webhook_token}"

# Error logging
except KeyError as e:
    logging.error(f"Missing environment variable: {e}")
    exit(1)
except ValueError:
    logging.error("REFRESH_TIME must be a valid integer.")
    exit(1)

# Display URLs and configurations
logging.info(f"GPU: {PRODUCT_NAME}")
logging.info(f"Discord Webhook URL: {wh_masked_url}")
logging.info(f"API URL SKU: {API_URL_SKU}")
logging.info(f"API URL Stock: {API_URL_STOCK}")
logging.info(f"Product URL: {PRODUCT_URL}")
logging.info(f"Refresh time: {REFRESH_TIME} seconds")
logging.info(f"Test Mode: {TEST_MODE}")

# HTTP headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9," 
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-GPC": "1",
}

# Session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Store stock status
global_stock_status = {}

# Store the last known SKU
last_sku = None
first_run = True  # Before calling check_rtx_50_founders

# Discord notifications
def send_discord_notification(gpu_name: str, product_link: str, products_price: str):
    
    # Get current UNIX timestamp
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: {gpu_name} available!")
        return
    
    embed = {
        "title": f"🚀 {PRODUCT_NAME} IN STOCK!",
        "color": 3066993,
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "author": {
            "name": "Nvidia Founder Editions"
        },

        "fields": [
            {
            "name": "Price",
            "value": f"`{products_price}€`",
            "inline": True
            },

            {
            "name": "Time",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            },
        ],
        "description": f"**:point_right: [Buy now]({product_link})**",
        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        }
    }
    payload = {"content": "@everyone", "username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification sent to Discord.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

def send_out_of_stock_notification(gpu_name: str, product_link: str, products_price: str):
    
    # Get current UNIX timestamp
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: {gpu_name} out of stock!")
        return
    
    embed = {
        "title": f"❌ {PRODUCT_NAME} is out of stock",
        "color": 15158332,  # Red for out of stock
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "url": f"{product_link}",
        "author": {
            "name": "Nvidia Founder Editions"
        },
        
        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },

        "fields": [
            {
            "name": "Time",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            }
        ]
    }
    payload = {"username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ 'Out of stock' notification sent to Discord.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

def send_sku_change_notification(old_sku: str, new_sku: str, product_link: str):
    
    # Get current UNIX timestamp
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] SKU change detected: {old_sku} → {new_sku}")
        return

    embed = {
        "title": f"🔄 {PRODUCT_NAME} SKU change detected",
        "url": f"{product_link}",
        "description": f"**Old SKU** : `{old_sku}`\n**New SKU** : `{new_sku}`",
        "color": 16776960,  # Yellow

        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },

        "fields": [
            {
            "name": "Time",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            }
        ]
    }
    
    payload = {
        "content": "@everyone ⚠️ Possible imminent drop!",
        "username": "NviBot",
        "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ SKU change notification sent to Discord.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

# Stock search
def check_rtx_50_founders():
    global global_stock_status, last_sku, first_run

    # Call product API to retrieve SKU and UPC
    try:
        response = session.get(API_URL_SKU, headers=HEADERS, timeout=10)
        logging.info(f"SKU API response: {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"SKU API error: {e}")
        return

   # Look for product whose GPU matches PRODUCT_NAME
    product_details = None

    for p in data['searchedProducts']['productDetails']:
        gpu_name = p.get("gpu", "").strip()
        
        # If the GPU matches exactly PRODUCT_NAME
        if gpu_name == PRODUCT_NAME.strip():
            product_details = p
            break  # Exit as soon as the correct product is found

    if not product_details:
        logging.warning(f"⚠️ No product with GPU '{PRODUCT_NAME}' found.")
        return

    # Retrieve the SKU for the found GPU
    product_sku = product_details['productSKU']
    product_upc = product_details.get('productUPC', "")

    # Check if this is the first execution
    if last_sku is not None and product_sku != last_sku:
        if not first_run:  # Prevent sending notification on first run
            product_link = PRODUCT_URL
            logging.warning(f"⚠️ SKU changed: {last_sku} → {product_sku}")
            send_sku_change_notification(last_sku, product_sku, product_link)

    # Update stored SKU
    last_sku = product_sku
    first_run = False  # Disable first-run protection

    if not isinstance(product_upc, list):
        product_upc = [product_upc]
    
    # Build stock API URL and call to check status
    API_URL = API_URL_STOCK + product_sku
    logging.info(f"Stock API URL called: {API_URL}")
    
    try:
        response = session.get(API_URL, headers=HEADERS, timeout=10)
        logging.info(f"Stock API response: {response.status_code}")  
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Stock API error: {e}")
        return

    products = data.get("listMap", [])
    products_price = 'Price not available'  # Default value

    # Check product list and retrieve price
    if isinstance(products, list) and len(products) > 0:
        for product in products:
            price = product.get("price", 'Price not available')
            if price != 'Price not available':
                products_price = price  # Use found price
                break  # Stop at first found price
    else:
        logging.error("Product list is empty or malformed.")

    found_in_stock = set()

    # Check status and send notifications accordingly
    for p in products:
        gpu_name = p.get("fe_sku", "").upper()
        is_active = p.get("is_active") == "true"
        if is_active and any(target.upper() in gpu_name for target in product_upc):
            found_in_stock.add(gpu_name)

    for gpu in product_upc:
        gpu_upper = gpu.upper()
        currently_in_stock = gpu_upper in found_in_stock
        previously_in_stock = global_stock_status.get(gpu_upper, False)
        
        if currently_in_stock and not previously_in_stock:
            product_link = PRODUCT_URL
            send_discord_notification(gpu_upper, product_link, products_price)
            global_stock_status[gpu_upper] = True
            logging.info(f"{gpu} is now in stock!")
        elif not currently_in_stock and previously_in_stock:
            product_link = PRODUCT_URL
            send_out_of_stock_notification(gpu_upper, product_link, products_price)
            global_stock_status[gpu_upper] = False
            logging.info(f"{gpu} is no longer in stock.")
        elif currently_in_stock and previously_in_stock:
            logging.info(f"{gpu} is currently in stock.")
        else:
            logging.info(f"{gpu} is currently out of stock.")

# Loop
if __name__ == "__main__":
    while True:
        check_rtx_50_founders()
        time.sleep(REFRESH_TIME)
