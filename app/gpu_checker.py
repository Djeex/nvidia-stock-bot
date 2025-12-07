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

    # Random delay to avoid pattern detection
    time.sleep(random.uniform(2, 6))

    # Fetching nvidia API data
    try:
        # Vary cache buster format to avoid pattern
        if random.choice([True, False]):
            cache_buster = f"v{random.randint(100, 999)}"
        else:
            cache_buster = f"{int(time.time() % 100000)}"
        sku_url = f"{API_URL_SKU}&cb={cache_buster}"
        
        response = session.get(sku_url, timeout=20)
        logging.info(f"SKU API response: {response.status_code}")
        if response.status_code == 429:
            logging.warning("Rate limited, waiting longer...")
            time.sleep(random.uniform(10, 20))
            return
        response.raise_for_status()
        
        # Debug response content
        logging.info(f"Content-Type: {response.headers.get('Content-Type')}")
        logging.info(f"Content-Encoding: {response.headers.get('Content-Encoding')}")
        logging.info(f"Response length: {len(response.content)}")
        
        try:
            data = response.json()
        except Exception as e:
            logging.error(f"JSON decode error: {e}")
            logging.error(f"Response content (first 200 chars): {response.text[:200]}")
            return
    except requests.exceptions.RequestException as e:
        logging.error(f"SKU API error: {e}")
        return
    
    # Checking productSKU and productUPC for all GPU set in PRODUCT_NAME
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

        # Detect SKU changes
        old_sku = last_sku_dict.get(product_name)
        if old_sku and old_sku != product_sku and not first_run_dict[product_name]:
            logging.warning(f"⚠️ SKU changed for {product_name}: {old_sku} → {product_sku}")
            send_sku_change_notification(product_name, old_sku, product_sku, PRODUCT_URL)

        last_sku_dict[product_name] = product_sku
        first_run_dict[product_name] = False
        
        # Random delay between requests
        time.sleep(random.uniform(1, 4))
        
        # Check product availability in API_URL_STOCK for each SKU
        if random.choice([True, False]):
            cache_param = f"v{random.randint(100, 999)}"
        else:
            cache_param = f"{int(time.time() % 100000)}"
        api_stock_url = f"{API_URL_STOCK}{product_sku}&cb={cache_param}"
        logging.info(f"[{product_name}] Checking stock: {api_stock_url}")

        try:
            response = session.get(api_stock_url, timeout=20)
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
