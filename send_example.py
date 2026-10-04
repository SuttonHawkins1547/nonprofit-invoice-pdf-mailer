"""Run a sample send: python send_example.py customer@example.org."""

import json
import sys
from decimal import Decimal

from receipt_sender import Invoice, send_invoice


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python send_example.py CUSTOMER_EMAIL")
    invoice = Invoice(
        number="NPO-2026-001",
        customer_email=sys.argv[1],
        organization="Neighborhood Food Pantry",
        description="Community meal sponsorship",
        amount=Decimal("75.00"),
    )
    print(json.dumps(send_invoice(invoice), indent=2))
