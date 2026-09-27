import json

from ecommerce_receipt import InfraiClient, Order, ReceiptService


class FakeResponse:
    status = 200
    headers = {}

    def read(self):
        return json.dumps({"ok": True, "data": {"id": "pdf-7"}, "error": None, "metadata": {}}).encode()


def test_paid_order_gets_receipt_before_update():
    captured = {}

    def opener(request):
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode())
        return FakeResponse()

    order = Order("ord-1", "a@example.com", "Notebook", 2, "18.00", "paid")
    result = ReceiptService(InfraiClient("test-key", opener)).process(order)
    assert result == {"order_id": "ord-1", "status": "shipped", "receipt": "pdf-7", "email": "a@example.com"}
    assert captured["method"] == "POST"
    assert captured["body"]["template_vars"]["quantity"] == 2
    assert captured["body"]["store"] is False


def test_unpaid_order_stays_pending():
    order = Order("ord-2", "a@example.com", "Notebook", 1, "9.00", "pending")
    result = ReceiptService(InfraiClient("unused", lambda request: None)).process(order)
    assert result["status"] == "awaiting_payment"
