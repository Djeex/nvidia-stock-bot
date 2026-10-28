import importlib
import sys

import pytest

MODULE_NAME = "env_config"

VALID_WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/abcdef"

ENV_KEYS = [
    "DISCORD_WEBHOOK_URL",
    "DISCORD_SERVER_NAME",
    "DISCORD_ROLES",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "COUNTRY",
    "REFRESH_TIME",
    "TEST_MODE",
    "PRODUCT_NAMES",
]


def _reload_env_config(monkeypatch, env):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def test_no_notification_channel_does_not_exit(monkeypatch, caplog):
    cfg = _reload_env_config(monkeypatch, {"PRODUCT_NAMES": "RTX 5090"})
    assert not cfg.DISCORD_ENABLED
    assert not cfg.TELEGRAM_ENABLED
    assert "DISCORD IS NOT CONFIGURED" in caplog.text
    assert "TELEGRAM IS NOT CONFIGURED" in caplog.text


def test_telegram_only_is_enabled(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch,
        {"PRODUCT_NAMES": "RTX 5090", "TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_CHAT_ID": "-100"},
    )
    assert cfg.TELEGRAM_ENABLED
    assert not cfg.DISCORD_ENABLED


def test_telegram_partial_config_is_disabled(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch, {"PRODUCT_NAMES": "RTX 5090", "TELEGRAM_BOT_TOKEN": "123:abc"}
    )
    assert not cfg.TELEGRAM_ENABLED


def test_missing_product_names_exits(monkeypatch):
    with pytest.raises(SystemExit):
        _reload_env_config(monkeypatch, {"DISCORD_WEBHOOK_URL": VALID_WEBHOOK})


def test_default_role_map_is_everyone(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch,
        {
            "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
            "PRODUCT_NAMES": "RTX 5090, RTX 5080",
        },
    )
    assert cfg.DISCORD_ROLE_MAP == {"RTX 5090": "@everyone", "RTX 5080": "@everyone"}


def test_role_count_mismatch_exits(monkeypatch):
    with pytest.raises(SystemExit):
        _reload_env_config(
            monkeypatch,
            {
                "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
                "PRODUCT_NAMES": "RTX 5090, RTX 5080",
                "DISCORD_ROLES": "<@&123456789012345678>",
            },
        )


def test_invalid_role_format_exits(monkeypatch):
    with pytest.raises(SystemExit):
        _reload_env_config(
            monkeypatch,
            {
                "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
                "PRODUCT_NAMES": "RTX 5090",
                "DISCORD_ROLES": "not-a-role",
            },
        )


def test_valid_role_format_accepted(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch,
        {
            "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
            "PRODUCT_NAMES": "RTX 5090",
            "DISCORD_ROLES": "<@&123456789012345678>",
        },
    )
    assert cfg.DISCORD_ROLE_MAP["RTX 5090"] == "<@&123456789012345678>"


def test_unknown_country_falls_back_to_us(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch,
        {
            "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
            "PRODUCT_NAMES": "RTX 5090",
            "COUNTRY": "ZZ",
        },
    )
    assert cfg.currency == "$"


def test_known_country_currency(monkeypatch):
    cfg = _reload_env_config(
        monkeypatch,
        {
            "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
            "PRODUCT_NAMES": "RTX 5090",
            "COUNTRY": "GB",
        },
    )
    assert cfg.currency == "£"


def test_refresh_time_invalid_exits(monkeypatch):
    with pytest.raises(SystemExit):
        _reload_env_config(
            monkeypatch,
            {
                "DISCORD_WEBHOOK_URL": VALID_WEBHOOK,
                "PRODUCT_NAMES": "RTX 5090",
                "REFRESH_TIME": "not-a-number",
            },
        )
