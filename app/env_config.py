import os
import re
import logging
import requests
from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.info("Script started")

# Load environment variables
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
DISCORD_SERVER_NAME = os.environ.get('DISCORD_SERVER_NAME', 'Shared for free')
API_URL_SKU = os.environ.get('API_URL_SKU', 'https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia')
API_URL_STOCK = os.environ.get('API_URL_STOCK', 'https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=')
PRODUCT_URL = os.environ.get('PRODUCT_URL', 'https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA')

REFRESH_TIME = int(os.environ.get('REFRESH_TIME', '60'))  # default 60 seconds if missing
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'

PRODUCT_NAMES = os.environ.get('PRODUCT_NAMES')
if not PRODUCT_NAMES:
    logging.error("❌ PRODUCT_NAMES is required but not defined.")
    exit(1)
PRODUCT_NAMES = [name.strip() for name in PRODUCT_NAMES.split(',')]

DISCORD_ROLES = os.environ.get('DISCORD_ROLES')

# Validate roles and map them to product names
DISCORD_ROLE_MAP = {}
if not DISCORD_ROLES or not DISCORD_ROLES.strip():
    logging.warning("⚠️ DISCORD_ROLES not defined or empty. Defaulting all roles to @everyone.")
    for name in PRODUCT_NAMES:
        DISCORD_ROLE_MAP[name] = '@everyone'
else:
    roles = [r.strip() if r.strip() else '@everyone' for r in DISCORD_ROLES.split(',')]
    if len(roles) != len(PRODUCT_NAMES):
        logging.error("❌ The number of DISCORD_ROLES must match PRODUCT_NAMES.")
        exit(1)
    for name, role in zip(PRODUCT_NAMES, roles):
        if role != '@everyone' and not re.match(r'^<@&\d{17,20}>$', role):
            logging.error(f"❌ Invalid DISCORD_ROLE format for {name}: {role}")
            exit(1)
        DISCORD_ROLE_MAP[name] = role

if not DISCORD_WEBHOOK_URL:
    logging.error("❌ DISCORD_WEBHOOK_URL is required but not defined.")
    exit(1)

# Mask webhook URL for logging
match = re.search(r'/(\d+)/(.*)', DISCORD_WEBHOOK_URL)
if match:
    webhook_id = match.group(1)
    webhook_token = match.group(2)
    masked_webhook_id = webhook_id[:len(webhook_id) - 10] + '*' * 10
    masked_webhook_token = webhook_token[:len(webhook_token) - 10] + '*' * 10
    wh_masked_url = f"https://discord.com/api/webhooks/{masked_webhook_id}/{masked_webhook_token}"
else:
    wh_masked_url = "Invalid Webhook URL"

logging.info(f"GPU: {PRODUCT_NAMES}")
logging.info(f"Discord Webhook URL: {wh_masked_url}")
logging.info(f"Discord Role Mention: {DISCORD_ROLES}")
logging.info(f"API URL SKU: {API_URL_SKU}")
logging.info(f"API URL Stock: {API_URL_STOCK}")
logging.info(f"Product URL: {PRODUCT_URL}")
logging.info(f"Refresh time: {REFRESH_TIME} seconds")
logging.info(f"Test Mode: {TEST_MODE}")

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

# Setup requests session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))