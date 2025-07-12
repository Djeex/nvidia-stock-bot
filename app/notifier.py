import time
import logging
import requests
from env_config import (
    DISCORD_WEBHOOK_URL, DISCORD_SERVER_NAME, DISCORD_ROLE_MAP, TEST_MODE, currency,
    in_stock_title, out_of_stock_title, sku_change_title,
    buy_now, price_label, time_label, footer, sku_description, imminent_drop
)

AVATAR = "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
THUMBNAIL = "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"

# In stock
def send_discord_notification(gpu_name, product_link, products_price):
    timestamp = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] Notification: {gpu_name} available!")
        return

    embed = {
        "title": in_stock_title.format(gpu_name=gpu_name),
        "color": 3066993,
        "thumbnail": {"url": THUMBNAIL},
        "author": {"name": "Nvidia Founder Editions"},
        "fields": [
            {"name": price_label, "value": f"`{currency}{products_price}`", "inline": True},
            {"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True}
        ],
        "description": buy_now.format(product_link=product_link),
        "footer": {"text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME), "icon_url": AVATAR}
    }

    payload = {
        "content": DISCORD_ROLE_MAP.get(gpu_name, "@everyone"),
        "username": "NviBot",
        "avatar_url": AVATAR,
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification sent to Discord.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

# Out of stock
def send_out_of_stock_notification(gpu_name, product_link, products_price):
    timestamp = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] Out of stock: {gpu_name}")
        return

    embed = {
        "title": out_of_stock_title.format(gpu_name=gpu_name),
        "color": 15158332,
        "thumbnail": {"url": THUMBNAIL},
        "url": product_link,
        "author": {"name": "Nvidia Founder Editions"},
        "footer": {"text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME), "icon_url": AVATAR},
        "fields": [{"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True}]
    }

    payload = {
        "username": "NviBot",
        "avatar_url": AVATAR,
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Out-of-stock notification sent.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

# SKU change
def send_sku_change_notification(gpu_name, old_sku, new_sku, product_link):
    timestamp = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] SKU change: {old_sku} → {new_sku}")
        return

    embed = {
        "title": sku_change_title.format(gpu_name=gpu_name),
        "url": product_link,
        "description": sku_description.format(old_sku=old_sku, new_sku=new_sku),
        "color": 16776960,
        "footer": {"text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME), "icon_url": AVATAR},
        "fields": [{"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True}]
    }

    payload = {
        "content": imminent_drop.format(DISCORD_ROLE=DISCORD_ROLE_MAP.get(gpu_name, '@everyone')),
        "username": "NviBot",
        "avatar_url": AVATAR,
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ SKU change notification sent.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")
        