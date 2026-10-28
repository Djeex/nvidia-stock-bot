import html
import logging
import re
import time

import requests

from env_config import (
    DISCORD_ENABLED,
    DISCORD_ROLE_MAP,
    DISCORD_SERVER_NAME,
    DISCORD_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
    TEST_MODE,
    buy_now,
    currency,
    footer,
    imminent_drop,
    in_stock_title,
    out_of_stock_title,
    price_label,
    sku_change_title,
    sku_description,
    time_label,
)

AVATAR = "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
THUMBNAIL = "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"


_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MD_CODE = re.compile(r"`(.+?)`")
_EMOJI_SHORTCODES = {":point_right:": "👉"}


def _md_to_telegram_html(text):
    """Convert the Discord markdown of the translations to Telegram HTML."""
    text = html.escape(text)
    text = _MD_LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = _MD_BOLD.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    text = _MD_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    for shortcode, emoji in _EMOJI_SHORTCODES.items():
        text = text.replace(shortcode, emoji)
    return text


# In stock
def send_discord_notification(gpu_name, product_link, products_price):
    if not DISCORD_ENABLED:
        return
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
            {"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True},
        ],
        "description": buy_now.format(product_link=product_link),
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": AVATAR,
        },
    }

    payload = {
        "content": DISCORD_ROLE_MAP.get(gpu_name, "@everyone"),
        "username": "NviBot",
        "avatar_url": AVATAR,
        "embeds": [embed],
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
    if not DISCORD_ENABLED:
        return
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
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": AVATAR,
        },
        "fields": [
            {"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True}
        ],
    }

    payload = {"username": "NviBot", "avatar_url": AVATAR, "embeds": [embed]}

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
    if not DISCORD_ENABLED:
        return
    timestamp = int(time.time())
    if TEST_MODE:
        logging.info(f"[TEST MODE] SKU change: {old_sku} → {new_sku}")
        return

    embed = {
        "title": sku_change_title.format(gpu_name=gpu_name),
        "url": product_link,
        "description": sku_description.format(old_sku=old_sku, new_sku=new_sku),
        "color": 16776960,
        "footer": {
            "text": footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME),
            "icon_url": AVATAR,
        },
        "fields": [
            {"name": time_label, "value": f"<t:{timestamp}:d> <t:{timestamp}:T>", "inline": True}
        ],
    }

    payload = {
        "content": imminent_drop.format(DISCORD_ROLE=DISCORD_ROLE_MAP.get(gpu_name, "@everyone")),
        "username": "NviBot",
        "avatar_url": AVATAR,
        "embeds": [embed],
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ SKU change notification sent.")
        else:
            logging.error(f"❌ Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Error sending webhook: {e}")


# Telegram
def _send_telegram(text, success_log):
    if TEST_MODE:
        logging.info(f"[TEST MODE] Telegram message: {text}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info(success_log)
        else:
            logging.error(f"❌ Telegram error: {response.status_code} - {response.text}")
    except Exception as e:
        # The exception message may contain the bot token (it is part of the URL)
        logging.error(f"🚨 Error sending Telegram message: {type(e).__name__}")


def _telegram_footer():
    return html.escape(footer.format(DISCORD_SERVER_NAME=DISCORD_SERVER_NAME))


def _telegram_time():
    return html.escape(time.strftime("%Y-%m-%d %H:%M:%S %Z"))


def send_telegram_notification(gpu_name, product_link, products_price):
    if not TELEGRAM_ENABLED:
        return
    title = html.escape(in_stock_title.format(gpu_name=gpu_name))
    description = _md_to_telegram_html(buy_now.format(product_link=product_link))
    price = html.escape(f"{currency}{products_price}")
    text = (
        f"<b>{title}</b>\n"
        f"{description}\n\n"
        f"{html.escape(price_label)}: <code>{price}</code>\n"
        f"{html.escape(time_label)}: {_telegram_time()}\n\n"
        f"<i>{_telegram_footer()}</i>"
    )
    _send_telegram(text, "✅ Notification sent to Telegram.")


def send_telegram_out_of_stock_notification(gpu_name, product_link, products_price):
    if not TELEGRAM_ENABLED:
        return
    title = html.escape(out_of_stock_title.format(gpu_name=gpu_name))
    text = (
        f'<b><a href="{html.escape(product_link)}">{title}</a></b>\n'
        f"{html.escape(time_label)}: {_telegram_time()}\n\n"
        f"<i>{_telegram_footer()}</i>"
    )
    _send_telegram(text, "✅ Out-of-stock notification sent to Telegram.")


def send_telegram_sku_change_notification(gpu_name, old_sku, new_sku, product_link):
    if not TELEGRAM_ENABLED:
        return
    alert = html.escape(imminent_drop.format(DISCORD_ROLE="").strip())
    title = html.escape(sku_change_title.format(gpu_name=gpu_name))
    description = _md_to_telegram_html(
        sku_description.format(old_sku=old_sku, new_sku=new_sku)
    )
    text = (
        f"{alert}\n"
        f'<b><a href="{html.escape(product_link)}">{title}</a></b>\n'
        f"{description}\n"
        f"{html.escape(time_label)}: {_telegram_time()}\n\n"
        f"<i>{_telegram_footer()}</i>"
    )
    _send_telegram(text, "✅ SKU change notification sent to Telegram.")
