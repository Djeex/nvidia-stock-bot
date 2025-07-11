import json
import logging
import os
import sys

required_keys = [
    "in_stock_title", "out_of_stock_title", "sku_change_title",
    "buy_now", "price", "time", "footer",
    "sku_description", "imminent_drop"
]

try:
    with open("localization.json", "r", encoding="utf-8") as f:
        localization = json.load(f)
except FileNotFoundError:
    logging.error("❌ localization.json file not found.")
    sys.exit(1)

language = os.environ.get("DISCORD_NOTIFICATION_LANGUAGE", "en").lower()
loc = localization.get(language)
fallback = localization.get("en")

if not loc:
    logging.warning(f"⚠️ Language '{language}' not found. Falling back to English.")
    loc = fallback

if not loc:
    logging.error("❌ No localization found for language 'en'. Cannot continue.")
    sys.exit(1)

missing_keys = [key for key in required_keys if key not in loc]
if missing_keys:
    logging.warning(f"⚠️ Missing keys in localization for '{language}': {', '.join(missing_keys)}. Falling back to English for those.")
    for key in missing_keys:
        if key in fallback:
            loc[key] = fallback[key]
        else:
            logging.error(f"❌ Missing required key '{key}' in both '{language}' and fallback 'en'.")
            sys.exit(1)

# Export localization strings for import convenience
in_stock_title = loc["in_stock_title"]
out_of_stock_title = loc["out_of_stock_title"]
sku_change_title = loc["sku_change_title"]
buy_now = loc["buy_now"]
price_label = loc["price"]
time_label = loc["time"]
footer = loc["footer"]
sku_description = loc["sku_description"]
imminent_drop = loc["imminent_drop"]