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
    DISCORD_ROLE = os.environ.get('DISCORD_ROLE', '@everyone').strip()
    API_URL_SKU = os.environ.get('API_URL_SKU', 'https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia')
    API_URL_STOCK = os.environ.get('API_URL_STOCK', 'https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=')
    REFRESH_TIME = int(os.environ.get('REFRESH_TIME'))
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    PRODUCT_URL = os.environ.get('PRODUCT_URL', 'https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA')
    PRODUCT_NAMES = os.environ.get('PRODUCT_NAMES')

    # Errors logging
    if not PRODUCT_NAMES:
        logging.error("❌ PRODUCT_NAMES is required but not defined.")
        exit(1)

    PRODUCT_NAMES = [name.strip() for name in PRODUCT_NAMES.split(',')]

    if DISCORD_ROLE != '@everyone' and not re.match(r'^<@&\d{17,20}>$', DISCORD_ROLE):
        logging.error("❌ DISCORD_ROLE format is invalid. Use '@everyone' or '<@&ROLE_ID>'.")
        exit(1)

    if not DISCORD_WEBHOOK_URL:
        logging.error("❌ DISCORD_WEBHOOK_URL is required but not defined.")
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
logging.info(f"GPU: {PRODUCT_NAMES}")
logging.info(f"Discord Webhook URL: {wh_masked_url}")
logging.info(f"Discord Role Mention: {DISCORD_ROLE}")
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

last_sku_dict = {}
global_stock_status_dict = {}
first_run_dict = {name: True for name in PRODUCT_NAMES}

# Discord notifications
def send_discord_notification(gpu_name: str, product_link: str, products_price: str):
    
    # Get current UNIX timestamp
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: {gpu_name} available!")
        return
    
    embed = {
        "title": f"🚀 {gpu_name} IN STOCK!",
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
    payload = {"content": f"{DISCORD_ROLE}", "username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg", "embeds": [embed]}
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
        "title": f"❌ {gpu_name} is out of stock",
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
        "title": f"🔄 {gpu_name} SKU change detected",
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
        "content": f"{DISCORD_ROLE} ⚠️ Possible imminent drop!",
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
    global last_sku_dict, global_stock_status_dict, first_run_dict

    try:
        response = session.get(API_URL_SKU, headers=HEADERS, timeout=10)
        logging.info(f"SKU API response: {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"SKU API error: {e}")
        return

    # All available products
    all_products = data['searchedProducts']['productDetails']

    for product_name in PRODUCT_NAMES:
        product_details = None
        for p in all_products:
            if p.get("gpu", "").strip() == product_name:
                product_details = p
                break

        if not product_details:
            logging.warning(f"⚠️ No product with GPU '{product_name}' found.")
            continue

        product_sku = product_details['productSKU']
        product_upc = product_details.get('productUPC', "")
        if not isinstance(product_upc, list):
            product_upc = [product_upc]

        # Check SKU change
        old_sku = last_sku_dict.get(product_name)
        if old_sku and old_sku != product_sku and not first_run_dict[product_name]:
            logging.warning(f"⚠️ SKU changed for {product_name}: {old_sku} → {product_sku}")
            send_sku_change_notification(old_sku, product_sku, PRODUCT_URL)

        last_sku_dict[product_name] = product_sku
        first_run_dict[product_name] = False

        # Stock check
        api_stock_url = API_URL_STOCK + product_sku
        logging.info(f"[{product_name}] Checking stock: {api_stock_url}")

        try:
            response = session.get(api_stock_url, headers=HEADERS, timeout=10)
            logging.info(f"[{product_name}] Stock API response: {response.status_code}")
            response.raise_for_status()
            stock_data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Stock API error: {e}")
            continue

        products = stock_data.get("listMap", [])
        products_price = "Price not available"
        if isinstance(products, list) and len(products) > 0:
            for p in products:
                price = p.get("price", 'Price not available')
                if price != 'Price not available':
                    products_price = price
                    break
        else:
            logging.error(f"[{product_name}] Product list is empty or malformed.")

        found_in_stock = set()
        for p in products:
            gpu_name = p.get("fe_sku", "").upper()
            is_active = p.get("is_active") == "true"
            if is_active and any(upc.upper() in gpu_name for upc in product_upc):
                found_in_stock.add(gpu_name)

        for upc in product_upc:
            upc_upper = upc.upper()
            currently_in_stock = upc_upper in found_in_stock
            previously_in_stock = global_stock_status_dict.get((product_name, upc_upper), False)

            if currently_in_stock and not previously_in_stock:
                send_discord_notification(product_name, PRODUCT_URL, products_price)
                global_stock_status_dict[(product_name, upc_upper)] = True
                logging.info(f"[{product_name}] {upc} is now in stock!")
            elif not currently_in_stock and previously_in_stock:
                send_out_of_stock_notification(product_name, PRODUCT_URL, products_price)
                global_stock_status_dict[(product_name, upc_upper)] = False
                logging.info(f"[{product_name}] {upc} is now out of stock.")
            elif currently_in_stock:
                logging.info(f"[{product_name}] {upc} still in stock.")
            else:
                logging.info(f"[{product_name}] {upc} still out of stock.")
# Loop
if __name__ == "__main__":
    try:
        while True:
            check_rtx_50_founders()
            time.sleep(REFRESH_TIME)

    # Gracefully shut down        
    except KeyboardInterrupt:
        logging.info("🛑 Script interrupted by user. Exiting gracefully.")
        exit(0)