import importlib
import sys

VALID_WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/abcdef"
PRODUCT_NAME = "RTX 5090 Founders Edition"

SKU_PAYLOAD = {
    "searchedProducts": {
        "productDetails": [{"gpu": PRODUCT_NAME, "productSKU": "SKU-1", "productUPC": "ABC123"}]
    }
}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def _stock_payload(in_stock, price="1999"):
    return {
        "listMap": [
            {"fe_sku": "ABC123", "is_active": "true" if in_stock else "false", "price": price}
        ]
    }


def _import_gpu_checker(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", VALID_WEBHOOK)
    monkeypatch.setenv("PRODUCT_NAMES", PRODUCT_NAME)
    monkeypatch.setenv("TEST_MODE", "True")
    monkeypatch.delenv("DISCORD_ROLES", raising=False)
    for mod in ("env_config", "notifier", "gpu_checker"):
        sys.modules.pop(mod, None)
    return importlib.import_module("gpu_checker")


def _queue_responses(monkeypatch, checker, *payloads):
    responses = [FakeResponse(p) for p in payloads]
    monkeypatch.setattr(checker.session, "get", lambda *a, **k: responses.pop(0))


def test_transition_to_in_stock_sends_notification(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)
    calls = []
    monkeypatch.setattr(
        checker, "send_discord_notification", lambda *a: calls.append(("in_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_out_of_stock_notification", lambda *a: calls.append(("out_of_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_sku_change_notification", lambda *a: calls.append(("sku_change", a))
    )

    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(True))
    checker.check_rtx_50_founders()

    assert len(calls) == 1
    assert calls[0][0] == "in_stock"
    assert calls[0][1][0] == PRODUCT_NAME


def test_transition_to_out_of_stock_sends_notification(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)
    calls = []
    monkeypatch.setattr(
        checker, "send_discord_notification", lambda *a: calls.append(("in_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_out_of_stock_notification", lambda *a: calls.append(("out_of_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_sku_change_notification", lambda *a: calls.append(("sku_change", a))
    )

    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(True))
    checker.check_rtx_50_founders()

    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(False))
    checker.check_rtx_50_founders()

    assert calls[-1][0] == "out_of_stock"
    assert calls[-1][1][0] == PRODUCT_NAME


def test_no_duplicate_notification_while_still_in_stock(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)
    calls = []
    monkeypatch.setattr(
        checker, "send_discord_notification", lambda *a: calls.append(("in_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_out_of_stock_notification", lambda *a: calls.append(("out_of_stock", a))
    )
    monkeypatch.setattr(
        checker, "send_sku_change_notification", lambda *a: calls.append(("sku_change", a))
    )

    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(True))
    checker.check_rtx_50_founders()
    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(True))
    checker.check_rtx_50_founders()

    assert len(calls) == 1


def test_sku_change_triggers_notification_after_first_run(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)
    sku_change_calls = []
    monkeypatch.setattr(checker, "send_discord_notification", lambda *a: None)
    monkeypatch.setattr(checker, "send_out_of_stock_notification", lambda *a: None)
    monkeypatch.setattr(
        checker, "send_sku_change_notification", lambda *a: sku_change_calls.append(a)
    )

    _queue_responses(monkeypatch, checker, SKU_PAYLOAD, _stock_payload(False))
    checker.check_rtx_50_founders()
    assert sku_change_calls == []  # first run must never fire a "change" notification

    changed_payload = {
        "searchedProducts": {
            "productDetails": [{"gpu": PRODUCT_NAME, "productSKU": "SKU-2", "productUPC": "ABC123"}]
        }
    }
    _queue_responses(monkeypatch, checker, changed_payload, _stock_payload(False))
    checker.check_rtx_50_founders()

    assert len(sku_change_calls) == 1
    assert sku_change_calls[0][1] == "SKU-1"
    assert sku_change_calls[0][2] == "SKU-2"


def test_missing_product_in_api_is_skipped_gracefully(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)
    calls = []
    monkeypatch.setattr(checker, "send_discord_notification", lambda *a: calls.append(a))

    empty_payload = {"searchedProducts": {"productDetails": []}}
    monkeypatch.setattr(checker.session, "get", lambda *a, **k: FakeResponse(empty_payload))

    checker.check_rtx_50_founders()  # must not raise, just log a warning and skip

    assert calls == []


def test_sku_api_error_is_handled_without_raising(monkeypatch):
    checker = _import_gpu_checker(monkeypatch)

    def raise_error(*a, **k):
        raise checker.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(checker.session, "get", raise_error)

    checker.check_rtx_50_founders()  # must not propagate the network error
