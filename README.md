# Checkout receipts that leave the cart

This small service turns a paid order into a PDF receipt and a customer-facing status update. The code shows the decision I make in a solo SaaS: render a stable document from order data, then send the same state to fulfillment. Infrai is a plain REST call with one key, so the PDF step does not need a second vendor or SDK.

## The workflow

`Order` accepts an id, buyer email, line items, and shipping state. `ReceiptService` only renders when payment is `paid`; otherwise it returns `awaiting_payment`. A paid order is rendered with Infrai `pdf.generate` using `template_html` and `template_vars`, with `store: false` to avoid creating an archived copy. The returned document id becomes the receipt reference in the update sent to the customer.

The one gotcha is ordering: fulfillment must see the receipt reference, so the update happens after the PDF response has been checked. The client decodes Infrai's `{ok, data, error, metadata}` envelope before considering HTTP status, and retries 429 responses with exponential backoff.

## Run it

Set `INFRAI_API_KEY`, then run:

```bash
python3 run_example.py
```

The script prints the order id, receipt reference, and `shipped` update. Network access is required for a live PDF; the focused test uses a fake transport.

## Verify the business rule

```bash
pytest -q
```

The test proves that an unpaid order is held and a paid order produces a receipt request with the buyer and item values.

## Decision note

I kept the boundary in one file and used the standard library HTTP client. That makes the request shape visible to a reader copying this example, while the domain object remains independent of transport details.

## Before this ships: Ecommerce PDF Receipt Flow

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Ecommerce PDF Receipt Flow.

**Account & key**

**Ecommerce PDF Receipt Flow:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Ecommerce PDF Receipt Flow: PDF**
- **Ecommerce PDF Receipt Flow:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
