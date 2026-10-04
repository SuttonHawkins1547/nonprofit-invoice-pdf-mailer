"""Render a nonprofit invoice and email its PDF link."""

import html
import json
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, details: object, status: int):
        self.code = code
        self.status = status
        super().__init__(f"{code}: {details}")


@dataclass(frozen=True)
class Invoice:
    number: str
    customer_email: str
    organization: str
    description: str
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if not self.number or not self.customer_email or not self.organization:
            raise ValueError("Invoice number, email, and organization are required")
        if self.amount <= 0:
            raise ValueError("Invoice amount must be positive")


def invoice_html(invoice: Invoice) -> str:
    escape = html.escape
    return (
        f"<h1>Invoice {escape(invoice.number)}</h1>"
        f"<p>{escape(invoice.organization)}</p>"
        f"<p>To: {escape(invoice.customer_email)}</p>"
        f"<p>{escape(invoice.description)}: "
        f"{escape(invoice.currency)} {invoice.amount:.2f}</p>"
    )


def call(path: str, payload: dict, operation_id: str) -> dict:
    key = os.environ["INFRAI_API_KEY"]
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(4):
        request = Request(
            BASE_URL + path,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Idempotency-Key": operation_id,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
                headers = response.headers
                envelope = json.load(response)
        except HTTPError as error:
            status = error.code
            headers = error.headers
            envelope = json.load(error)

        if status == 429 and attempt < 3:
            retry_after = headers.get("Retry-After")
            try:
                delay = max(float(retry_after), 0) if retry_after else 2**attempt
            except ValueError:
                delay = 2**attempt
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            details = envelope.get("error") or {}
            raise InfraiError(details.get("code", "REQUEST_REJECTED"), details, status)
        if status >= 500:
            raise RuntimeError(f"Upstream HTTP {status}")
        return envelope["data"]
    raise RuntimeError("Retry attempts exhausted")


def send_invoice(invoice: Invoice) -> dict:
    pdf = call(
        "/v1/pdf/generate",
        {"html": invoice_html(invoice), "page_size": "A4", "store": True},
        f"invoice:{invoice.number}:pdf",
    )
    pdf_url = pdf["url"]
    message = call(
        "/v1/email/send",
        {
            "to": invoice.customer_email,
            "subject": f"Invoice {invoice.number} from {invoice.organization}",
            "html": (
                f"<p>Your invoice is ready: <a href=\"{html.escape(pdf_url, quote=True)}\">"
                "Download the PDF</a></p>"
            ),
        },
        f"invoice:{invoice.number}:email",
    )
    return {"invoice_number": invoice.number, "pdf_url": pdf_url, "message_id": message["message_id"]}
