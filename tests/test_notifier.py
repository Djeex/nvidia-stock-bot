import importlib
import sys

VALID_WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/abcdef"


def _import_notifier(monkeypatch, test_mode="False", discord_roles=None):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", VALID_WEBHOOK)
    monkeypatch.setenv("PRODUCT_NAMES", "RTX 5090 Founders Edition")
    monkeypatch.setenv("TEST_MODE", test_mode)
    if discord_roles is not None:
        monkeypatch.setenv("DISCORD_ROLES", discord_roles)
    else:
        monkeypatch.delenv("DISCORD_ROLES", raising=False)
    for mod in ("env_config", "notifier"):
        sys.modules.pop(mod, None)
    return importlib.import_module("notifier")


class FakeResponse:
    def __init__(self, status_code=204, text=""):
        self.status_code = status_code
        self.text = text


def test_test_mode_skips_network_call(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="True")
    calls = []
    monkeypatch.setattr(notifier.requests, "post", lambda *a, **k: calls.append((a, k)))

    notifier.send_discord_notification("RTX 5090 Founders Edition", "https://example.com", "1999")

    assert calls == []


def test_in_stock_notification_posts_expected_payload(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")
    captured = {}

    def fake_post(url, json=None, **kwargs):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    notifier.send_discord_notification(
        "RTX 5090 Founders Edition", "https://example.com/buy", "1999"
    )

    assert captured["url"] == notifier.DISCORD_WEBHOOK_URL
    assert captured["json"]["content"] == "@everyone"
    embed = captured["json"]["embeds"][0]
    assert "RTX 5090 Founders Edition" in embed["title"]


def test_discord_notification_survives_http_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")
    monkeypatch.setattr(
        notifier.requests, "post", lambda *a, **k: FakeResponse(status_code=500, text="boom")
    )

    notifier.send_discord_notification("RTX 5090 Founders Edition", "https://example.com", "1999")


def test_discord_notification_survives_connection_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")

    def raise_error(*a, **k):
        raise notifier.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(notifier.requests, "post", raise_error)

    # Should not raise even though the request itself blew up (network down, DNS, etc.)
    notifier.send_discord_notification("RTX 5090 Founders Edition", "https://example.com", "1999")


def test_out_of_stock_test_mode_skips_network_call(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="True")
    calls = []
    monkeypatch.setattr(notifier.requests, "post", lambda *a, **k: calls.append((a, k)))

    notifier.send_out_of_stock_notification(
        "RTX 5090 Founders Edition", "https://example.com", "1999"
    )

    assert calls == []


def test_out_of_stock_notification_posts_on_success(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")
    captured = {}

    def fake_post(url, json=None, **kwargs):
        captured["json"] = json
        return FakeResponse(status_code=204)

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    notifier.send_out_of_stock_notification(
        "RTX 5090 Founders Edition", "https://example.com/buy", "1999"
    )

    assert captured["json"]["embeds"][0]["url"] == "https://example.com/buy"


def test_out_of_stock_notification_survives_http_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")
    monkeypatch.setattr(
        notifier.requests, "post", lambda *a, **k: FakeResponse(status_code=500, text="boom")
    )

    # Should not raise even though the webhook call "fails"
    notifier.send_out_of_stock_notification(
        "RTX 5090 Founders Edition", "https://example.com", "1999"
    )


def test_out_of_stock_notification_survives_connection_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")

    def raise_error(*a, **k):
        raise notifier.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(notifier.requests, "post", raise_error)

    notifier.send_out_of_stock_notification(
        "RTX 5090 Founders Edition", "https://example.com", "1999"
    )


def test_sku_change_test_mode_skips_network_call(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="True")
    calls = []
    monkeypatch.setattr(notifier.requests, "post", lambda *a, **k: calls.append((a, k)))

    notifier.send_sku_change_notification(
        "RTX 5090 Founders Edition", "old-sku", "new-sku", "https://example.com"
    )

    assert calls == []


def test_sku_change_notification_survives_http_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")
    monkeypatch.setattr(
        notifier.requests, "post", lambda *a, **k: FakeResponse(status_code=500, text="boom")
    )

    notifier.send_sku_change_notification(
        "RTX 5090 Founders Edition", "old-sku", "new-sku", "https://example.com"
    )


def test_sku_change_notification_survives_connection_error(monkeypatch):
    notifier = _import_notifier(monkeypatch, test_mode="False")

    def raise_error(*a, **k):
        raise notifier.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(notifier.requests, "post", raise_error)

    notifier.send_sku_change_notification(
        "RTX 5090 Founders Edition", "old-sku", "new-sku", "https://example.com"
    )


def test_sku_change_notification_mentions_role_and_skus(monkeypatch):
    notifier = _import_notifier(
        monkeypatch, test_mode="False", discord_roles="<@&123456789012345678>"
    )
    captured = {}

    def fake_post(url, json=None, **kwargs):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    notifier.send_sku_change_notification(
        "RTX 5090 Founders Edition", "old-sku-123", "new-sku-456", "https://example.com"
    )

    assert "<@&123456789012345678>" in captured["json"]["content"]
    description = captured["json"]["embeds"][0]["description"]
    assert "old-sku-123" in description
    assert "new-sku-456" in description
