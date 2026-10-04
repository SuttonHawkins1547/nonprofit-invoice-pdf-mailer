from decimal import Decimal
from unittest.mock import patch

import pytest

from receipt_sender import Invoice, invoice_html, send_invoice


def test_invoice_amount_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        Invoice("NPO-2", "donor@example.org", "Food Pantry", "Gift", Decimal("0"))


def test_pdf_handoff_uses_generated_url_and_same_request_boundary():
    invoice = Invoice("NPO-2", "donor@example.org", "Food Pantry", "Gift", Decimal("25"))
    with patch("receipt_sender.call", side_effect=[
        {"url": "https://files.example.org/invoice.pdf"},
        {"message_id": "msg-123"},
    ]) as request:
        result = send_invoice(invoice)

    assert result["message_id"] == "msg-123"
    assert request.call_args_list[0].args[1]["html"] == invoice_html(invoice)
    assert request.call_args_list[1].args[1]["to"] == "donor@example.org"
    assert "https://files.example.org/invoice.pdf" in request.call_args_list[1].args[1]["html"]
    assert request.call_args_list[0].args[2] != request.call_args_list[1].args[2]
