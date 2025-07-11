import logging
from env_config import session, API_URL_SKU, API_URL_STOCK, PRODUCT_NAMES

def get_current_skus():
    try:
        response = session.get(API_URL_SKU)
        response.raise_for_status()
        data = response.json()
        sku_map = {}
        for product in data.get('products', []):
            name = product.get('name')
            sku = product.get('productSKU')
            if name and sku and any(pn.lower() in name.lower() for pn in PRODUCT_NAMES):
                sku_map[name] = sku
        logging.info(f"✅ Fetched current SKUs: {sku_map}")
        return sku_map
    except Exception as e:
        logging.error(f"🚨 Error fetching SKUs: {e}")
        return {}

def check_stock_for_skus(skus):
    try:
        sku_list = ','.join(skus)
        url = f"{API_URL_STOCK}{sku_list}"
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        stock_status = {}
        for sku_data in data.get('inventory', []):
            sku = sku_data.get('sku')
            available = sku_data.get('availability') == 'IN_STOCK'
            price = sku_data.get('price', 'N/A')
            stock_status[sku] = {'available': available, 'price': price}
        logging.info(f"✅ Stock check results: {stock_status}")
        return stock_status
    except Exception as e:
        logging.error(f"🚨 Error checking stock: {e}")
        return {}