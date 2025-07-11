import os
import re
import logging
import json
import sys

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.info("Script started")

try:
    # Env variables
    DISCORD_WEBHOOK_URL = os.environ['DISCORD_WEBHOOK_URL']
    DISCORD_SERVER_NAME = os.environ.get('DISCORD_SERVER_NAME', 'Shared for free')
    API_URL_SKU = os.environ.get('API_URL_SKU', 'https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia')
    API_URL_STOCK = os.environ.get('API_URL_STOCK', 'https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=')
    REFRESH_TIME = int(os.environ['REFRESH_TIME'])
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    PRODUCT_URL = os.environ.get('PRODUCT_URL', 'https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA')
    DISCORD_ROLES = os.environ.get('DISCORD_ROLES')
    PRODUCT_NAMES = os.environ['PRODUCT_NAMES']
except KeyError as e:
    logging.error(f"Missing environment variable: {e}")
    sys.exit(1)
except ValueError:
    logging.error("REFRESH_TIME must be a valid integer.")
    sys.exit(1)

if not PRODUCT_NAMES:
    logging.error("❌ PRODUCT_NAMES is required but not defined.")
    sys.exit(1)

PRODUCT_NAMES = [name.strip() for name in PRODUCT_NAMES.split(',')]

# Role mapping
DISCORD_ROLE_MAP = {}
if not DISCORD_ROLES or not DISCORD_ROLES.strip():
    logging.warning("⚠️ DISCORD_ROLES not defined or empty. Defaulting all roles to @everyone.")
    for name in PRODUCT_NAMES:
        DISCORD_ROLE_MAP[name] = '@everyone'
else:
    roles = [r.strip() if r.strip() else '@everyone' for r in DISCORD_ROLES.split(',')]
    if len(roles) != len(PRODUCT_NAMES):
        logging.error("❌ The number of DISCORD_ROLES must match PRODUCT_NAMES.")
        sys.exit(1)
    for name, role in zip(PRODUCT_NAMES, roles):
        if role != '@everyone' and not re.match(r'^<@&\d{17,20}>$', role):
            logging.error(f"❌ Invalid DISCORD_ROLE format for {name}: {role}")
            sys.exit(1)
        DISCORD_ROLE_MAP[name] = role

if not DISCORD_WEBHOOK_URL:
    logging.error("❌ DISCORD_WEBHOOK_URL is required but not defined.")
    sys.exit(1)

# Masked webhook for display
match = re.search(r'/(\d+)/(.*)', DISCORD_WEBHOOK_URL)
if match:
    webhook_id = match.group(1)
    webhook_token = match.group(2)
    masked_webhook_id = webhook_id[:len(webhook_id) - 10] + '*' * 10
    masked_webhook_token = webhook_token[:len(webhook_token) - 120] + '*' * 10
    wh_masked_url = f"https://discord.com/api/webhooks/{masked_webhook_id}/{masked_webhook_token}"
else:
    wh_masked_url = "[Invalid webhook URL]"

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

# Localization loading
language = os.environ.get("DISCORD_NOTIFICATION_LANGUAGE", "en").lower()
try:
    with open("localization.json", "r", encoding="utf-8") as f:
        localization = json.load(f)
except FileNotFoundError:
    logging.error("❌ localization.json file not found.")
    sys.exit(1)

required_keys = [
    "in_stock_title", "out_of_stock_title", "sku_change_title",
    "buy_now", "price", "time", "footer",
    "sku_description", "imminent_drop"
]
loc = localization.get(language, localization.get("en", {}))
logging.info(f"Notification language: {language}")

if not loc:
    logging.warning(f"⚠️ Language '{language}' not found. Falling back to English.")
    loc = localization.get("en", {})
    language = "en"

missing_keys = [key for key in required_keys if key not in loc]
fallback = localization.get("en", {})
for key in missing_keys:
    if key in fallback:
        loc[key] = fallback[key]
    else:
        logging.error(f"❌ Missing required key '{key}' in both '{language}' and fallback 'en'.")
        sys.exit(1)

# Public constants
in_stock_title = loc["in_stock_title"]
out_of_stock_title = loc["out_of_stock_title"]
sku_change_title = loc["sku_change_title"]
buy_now = loc["buy_now"]
price_label = loc["price"]
time_label = loc["time"]
footer = loc["footer"]
sku_description = loc["sku_description"]
imminent_drop = loc["imminent_drop"]

logging.info(f"GPU: {PRODUCT_NAMES}")
logging.info(f"Discord Webhook URL: {wh_masked_url}")
logging.info(f"Discord Role Mention: {DISCORD_ROLES}")
logging.info(f"API URL SKU: {API_URL_SKU}")
logging.info(f"API URL Stock: {API_URL_STOCK}")
logging.info(f"Product URL: {PRODUCT_URL}")
logging.info(f"Refresh time: {REFRESH_TIME} seconds")
logging.info(f"Test Mode: {TEST_MODE}")
