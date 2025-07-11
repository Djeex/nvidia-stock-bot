import time
import logging
import requests
from env_config import DISCORD_WEBHOOK_URL, DISCORD_ROLE_MAP, TEST_MODE, DISCORD_SERVER_NAME
from localization import (
    in_stock_title, out_of_stock_title, sku_change_title,
    buy_now, price_label, time_label, footer,
    sku_description, imminent_drop
)

def send_discord_notification(gpu_name: str, product_link: str, products_price: str):
    timestamp_unix = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: {gpu_name} available!")
        return

    embed = {
        "title": in_stock_title.format(gpu_name=gpu_name),
        "color": 3066993,
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "author": {
            "name": "Nvidia Founder Editions"
        },
        "fields": [
            {
                "name": price_label,
                "value": f"`{products_price}€`",
                "inline": True
            },
            {
                "name": time_label,
                "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
                "inline": True
            },
        ],
        "description": buy_now.format(product_link=product_link),
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        }
    }

    payload = {
        "content": DISCORD_ROLE_MAP.get(gpu_name, '@everyone'),
        "username": "NviBot",
        "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg",
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

def send_out_of_stock_notification(gpu_name: str, product_link: str, products_price: str):
    timestamp_unix = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: {gpu_name} out of stock!")
        return

    embed = {
        "title": out_of_stock_title.format(gpu_name=gpu_name),
        "color": 15158332,
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "url": product_link,
        "author": {
            "name": "Nvidia Founder Editions"
        },
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },
        "fields": [
            {
                "name": time_label,
                "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
                "inline": True
            }
        ]
    }
    payload = {
        "username": "NviBot",
        "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg",
        "embeds": [embed]
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ 'Out of stock' notification sent to Discord.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")

def send_sku_change_notification(gpu_name: str, old_sku: str, new_sku: str, product_link: str):
    timestamp_unix = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] Discord Notification: SKU change for {gpu_name}: {old_sku} -> {new_sku}")
        return

    embed = {
        "title": sku_change_title.format(gpu_name=gpu_name),
        "color": 3447003,
        "author": {
            "name": "Nvidia Founder Editions"
        },
        "description": sku_description.format(old_sku=old_sku, new_sku=new_sku),
        "url": product_link,
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },
        "fields": [
            {
                "name": time_label,
                "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
                "inline": True
            }
        ]
    }
    payload = {
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