import os
import re
import logging
import json
import sys

# Read version from VERSION file
with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION"), "r", encoding="utf-8") as f:
    VERSION = f.read().strip()

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Logging starter
logging.info("=" * 60)
logging.info("🟩 Nvidia Stock Bot - Version %s", VERSION)
logging.info("Source: https://git.djeex.fr/Djeex/nvidia-stock-bot")
logging.info("Mirror: https://github.com/Djeex/nvidia-stock-bot")
logging.info("=" * 60)

# Env variables
try:
    DISCORD_WEBHOOK_URL = os.environ['DISCORD_WEBHOOK_URL']
    DISCORD_SERVER_NAME = os.environ.get('DISCORD_SERVER_NAME', 'Shared for free')
    DISCORD_ROLES = os.environ.get('DISCORD_ROLES')
    COUNTRY = os.environ.get('COUNTRY') or 'US'
    REFRESH_TIME = int(os.environ.get('REFRESH_TIME') or 30)
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    PRODUCT_NAMES = os.environ['PRODUCT_NAMES']

# Errors and warning
except KeyError as e:
    logging.error(f"Missing environment variable: {e}")
    sys.exit(1)
except ValueError:
    logging.error("REFRESH_TIME must be a valid integer.")
    sys.exit(1)

if TEST_MODE:
    logging.warning("🚧 Test mode is active. No real alerts will be sent.")

if not PRODUCT_NAMES:
    logging.error("❌ PRODUCT_NAMES is required but not defined.")
    sys.exit(1)
if not DISCORD_WEBHOOK_URL:
    logging.error("❌ DISCORD_WEBHOOK_URL is required but not defined.")
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

# Masked webhook in terminal
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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://partners.nvidia.com/",
    "Origin": "https://partners.nvidia.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not.A/Brand\";v=\"24\"",
    "Sec-Ch-Ua-Platform": "\"macOS\"",
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

# Load country setting and localization config
country_code = os.environ.get("COUNTRY", "US").upper()

try:
    with open("localization.json", "r", encoding="utf-8") as f:
        localization_config = json.load(f)
except FileNotFoundError:
    logging.error("❌ localization.json file not found.")
    sys.exit(1)

# Find country entry
country_entry = next((entry for entry in localization_config if entry["country_code"].upper() == country_code), None)

if not country_entry:
    logging.warning(f"⚠️ Country '{country_code}' not found in localization.json. Defaulting to US.")
    country_entry = next((entry for entry in localization_config if entry["country_code"].upper() == "US"), None)
    if not country_entry:
        logging.error("❌ US fallback not found in localization.json.")
        sys.exit(1)

# Extract language code and currency
full_lang_code = country_entry["language_code"]
language = full_lang_code[:2].lower()  # e.g., "en-US" -> "en"
currency = country_entry["currency"]

# Load language file
try:
    with open("languages.json", "r", encoding="utf-8") as f:
        loc_lang = json.load(f)
except FileNotFoundError:
    logging.error("❌ languages.json file not found.")
    sys.exit(1)

loc = loc_lang.get(language, loc_lang.get("en", {}))
logging.info(f"Notification language: {language} (from country {country_code})")
logging.info(f"Currency symbol: {currency}")

if not loc:
    logging.warning(f"⚠️ Language '{language}' not found. Falling back to English.")
    loc = loc_lang.get("en", {})
    language = "en"

# Ensure all required keys are present
required_keys = [
    "in_stock_title", "out_of_stock_title", "sku_change_title",
    "buy_now", "price", "time", "footer",
    "sku_description", "imminent_drop"
]
missing_keys = [key for key in required_keys if key not in loc]
fallback = loc_lang.get("en", {})

for key in missing_keys:
    if key in fallback:
        loc[key] = fallback[key]
    else:
        logging.error(f"❌ Missing required key '{key}' in both '{language}' and fallback 'en'.")
        sys.exit(1)

# Localized API - Env var can be overrided for development purposes
locale = full_lang_code.lower()
API_URL_SKU = os.getenv(
    "API_URL_SKU",
    f"https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale={locale}&Manufacturer=Nvidia"
)

API_URL_STOCK = os.getenv(
    "API_URL_STOCK",
    f"https://api.store.nvidia.com/partner/v1/feinventory?locale={locale}&skus="
)

PRODUCT_URL = os.getenv(
    "PRODUCT_URL",
    f"https://marketplace.nvidia.com/{locale}/consumer/graphics-cards/?locale={locale}&page=1&limit=12&manufacturer=NVIDIA"
)

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

# Logging
logging.info(f"GPU: {PRODUCT_NAMES}")
logging.info(f"Discord Webhook URL: {wh_masked_url}")
logging.info(f"Discord Role Mention: {DISCORD_ROLES}")
logging.info(f"API URL SKU: {API_URL_SKU}")
logging.info(f"API URL Stock: {API_URL_STOCK}")
logging.info(f"Product URL: {PRODUCT_URL}")
logging.info(f"Refresh time: {REFRESH_TIME} seconds")
logging.info(f"Test Mode: {TEST_MODE}")
