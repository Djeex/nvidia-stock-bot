import requests
import logging
import time
import random
from env_config import HEADERS, PRODUCT_NAMES, API_URL_SKU, API_URL_STOCK, PRODUCT_URL
from notifier import send_discord_notification, send_out_of_stock_notification, send_sku_change_notification
from requests.adapters import HTTPAdapter, Retry

# HTTP session with stealth configuration
session = requests.Session()
retries = Retry(total=2, backoff_factor=3, status_forcelist=[500, 502, 503, 504, 429])
adapter = HTTPAdapter(max_retries=retries, pool_connections=1, pool_maxsize=1)
session.mount('https://', adapter)
session.headers.update(HEADERS)

# Keeping memory of last run 
last_sku_dict = {}
global_stock_status_dict = {}
first_run_dict = {name: True for name in PRODUCT_NAMES}

# Stock check function
def check_rtx_50_founders():
    global last_sku_dict, global_stock_status_dict, first_run_dict

    # First get Akamai cookie by visiting main site
    try:
        logging.info("Getting Akamai protection cookie...")
        session.get("https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/", timeout=10)
        time.sleep(1)  # Let the session establish
    except Exception as e:
        logging.warning(f"Failed to get initial cookie: {e}")

    # Fetching nvidia API data
    try:
        sku_url = API_URL_SKU
        
        response = session.get(sku_url, timeout=10)
        logging.info(f"SKU API response: {response.status_code}")
        if response.status_code == 429:
            logging.warning("Rate limited, waiting longer...")
            time.sleep(random.uniform(10, 20))
            return
        response.raise_for_status()
        
        # Debug response content
        logging.info(f"Content-Type: {response.headers.get('Content-Type')}")
        logging.info(f"Content-Length: {response.headers.get('Content-Length')}")
        logging.info(f"Response text length: {len(response.text)}")
        logging.info(f"Response content (first 300 chars): {response.text[:300]}")
        
        # Check if content looks like JSON
        if not response.text.strip().startswith('{'):
            logging.error("Response doesn't start with '{' - not JSON!")
            logging.error(f"Full response: {response.text}")
            return
            
        try:
            data = response.json()
        except Exception as e:
            logging.error(f"JSON decode error: {e}")
            logging.error(f"Full response text: {response.text}")
            return
    except requests.exceptions.ReadTimeout:
        logging.error("Read timeout - IP may be rate limited/blocked. Try changing IP or wait several hours.")
        return
    except requests.exceptions.ConnectionError as e:
        if "Failed to resolve" in str(e):
            logging.error("DNS resolution failed - IP may be DNS blacklisted. Try VPN or different DNS servers.")
        else:
            logging.error(f"Connection error: {e}")
        return
    except requests.exceptions.RequestException as e:
        logging.error(f"SKU API error: {e}")
        return
    
    # Checking productSKU and productUPC for all GPU set in PRODUCT_NAME
    all_products = data['searchedProducts']['productDetails']

    for product_name in PRODUCT_NAMES:
        product_details = None
        for p in all_products:
            gpu_name = p.get("gpu", "").strip()
            # Flexible matching: exact match or partial match
            if gpu_name == product_name or product_name in gpu_name:
                product_details = p
                break

        if not product_details:
            logging.warning(f"⚠️ No product with GPU '{product_name}' found.")
            # Debug: show available GPU names for troubleshooting
            available_gpus = set(p.get("gpu", "") for p in all_products if p.get("gpu"))
            logging.info(f"Available GPUs: {sorted(list(available_gpus))[:10]}")  # Show first 10
            continue

        product_sku = product_details['productSKU']
        product_upc = product_details.get('productUPC', "")
        if not isinstance(product_upc, list):
            product_upc = [product_upc]

        # Detect SKU changes
        old_sku = last_sku_dict.get(product_name)
        if old_sku and old_sku != product_sku and not first_run_dict[product_name]:
            logging.warning(f"⚠️ SKU changed for {product_name}: {old_sku} → {product_sku}")
            send_sku_change_notification(product_name, old_sku, product_sku, PRODUCT_URL)

        last_sku_dict[product_name] = product_sku
        first_run_dict[product_name] = False
        
        # Check product availability in API_URL_STOCK for each SKU
        api_stock_url = f"{API_URL_STOCK}{product_sku}"
        logging.info(f"[{product_name}] Checking stock: {api_stock_url}")

        try:
            response = session.get(api_stock_url, timeout=10)
            logging.info(f"[{product_name}] Stock API response: {response.status_code}")
            if response.status_code == 429:
                logging.warning(f"[{product_name}] Rate limited, skipping...")
                continue
            response.raise_for_status()
            stock_data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Stock API error: {e}")
            continue

        # Retrieve availibilty and price for each SKU
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
        
        # Comparing previous state and notify
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
