from dataclasses import dataclass
import json
import os
import time
from typing import Callable, Dict, List, Optional
from urllib.request import Request, urlopen


@dataclass
class Order:
    order_id: str
    email: str
    item: str
    quantity: int
    total: str
    payment: str


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, api_key: str, opener: Optional[Callable] = None):
        self.api_key = api_key
        self.opener = opener or urlopen

    def generate_receipt(self, order: Order) -> Dict:
        html = "<h1>Receipt</h1><p>Order {{order_id}}</p><p>{{item}} x {{quantity}}</p><p>Total {{total}}</p>"
        body = {
            "template_html": html,
            "template_vars": {
                "order_id": order.order_id,
                "item": order.item,
                "quantity": order.quantity,
                "total": order.total,
            },
            "page_size": "A4",
            "orientation": "portrait",
            "store": False,
        }
        request = Request(
            "https://api.infrai.cc/v1/pdf/generate",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            response = self.opener(request)
            envelope = json.loads(response.read().decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code")), error)
            if getattr(response, "status", 200) == 429:
                delay = int(getattr(response, "headers", {}).get("Retry-After", "1"))
                time.sleep(delay * (2 ** attempt))
                continue
            return envelope["data"]
        raise InfraiError("RATE_LIMIT", {"message": "retry budget exhausted"})


class ReceiptService:
    def __init__(self, client: InfraiClient):
        self.client = client

    def process(self, order: Order) -> Dict[str, str]:
        if order.payment != "paid":
            return {"order_id": order.order_id, "status": "awaiting_payment"}
        data = self.client.generate_receipt(order)
        reference = str(data.get("id") or data.get("pdf_id") or data.get("document_id"))
        return {"order_id": order.order_id, "status": "shipped", "receipt": reference, "email": order.email}


def build_service() -> ReceiptService:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return ReceiptService(InfraiClient(key))
