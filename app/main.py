import time
import logging
from env_config import REFRESH_TIME, PRODUCT_NAMES, PRODUCT_URL
from gpu_checker import get_current_skus, check_stock_for_skus
from notifier import send_discord_notification, send_out_of_stock_notification, send_sku_change_notification

def main():
    previous_sku_map = {}
    while True:
        try:
            current_sku_map = get_current_skus()
            if not current_sku_map:
                logging.warning("⚠️ No SKUs found, skipping this cycle.")
                time.sleep(REFRESH_TIME)
                continue

            sku_list = list(current_sku_map.values())
            stock_data = check_stock_for_skus(sku_list)
            if not stock_data:
                logging.warning("⚠️ No stock data found, skipping this cycle.")
                time.sleep(REFRESH_TIME)
                continue

            for gpu_name in PRODUCT_NAMES:
                old_sku = previous_sku_map.get(gpu_name)
                new_sku = current_sku_map.get(gpu_name)

                # Detect SKU changes
                if old_sku and new_sku and old_sku != new_sku:
                    send_sku_change_notification(gpu_name, old_sku, new_sku, PRODUCT_URL)

                sku_to_check = new_sku or old_sku
                if sku_to_check and sku_to_check in stock_data:
                    availability = stock_data[sku_to_check]['available']
                    price = stock_data[sku_to_check]['price']
                    if availability:
                        send_discord_notification(gpu_name, PRODUCT_URL, price)
                    else:
                        send_out_of_stock_notification(gpu_name, PRODUCT_URL, price)

            previous_sku_map = current_sku_map
            logging.info(f"Waiting {REFRESH_TIME}s before next check...")
            time.sleep(REFRESH_TIME)

        except KeyboardInterrupt:
            logging.info("Stopping script due to keyboard interrupt.")
            break
        except Exception as e:
            logging.error(f"🚨 Unexpected error: {e}")
            time.sleep(REFRESH_TIME)

if __name__ == "__main__":
    main()