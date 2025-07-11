import requests
import logging
from env_config import API_URL_SKU, API_URL_STOCK, HEADERS, PRODUCT_NAMES, PRODUCT_URL
from notifier import send_discord_notification, send_out_of_stock_notification, send_sku_change_notification

from requests.adapters import HTTPAdapter, Retry

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

last_sku_dict = {}
global_stock_status_dict = {}
first_run_dict = {name: True for name in PRODUCT_NAMES}

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
            send_sku_change_notification(product_name, old_sku, product_sku, PRODUCT_URL)

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
                