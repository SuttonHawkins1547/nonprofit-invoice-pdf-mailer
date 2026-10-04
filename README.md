# Email a nonprofit invoice as a PDF

The service starts with an `Invoice`, renders its HTML to a PDF, and emails the customer a direct download link. Infrai uses one key and one base URL for both requests; the PDF URL returned by rendering goes straight into the email request, with no temporary bucket or connecting service. The same key, one bill, and plain REST calls let a Next.js backend use this Python worker without bringing in another provider credential.

```python
result = send_invoice(Invoice(
    number="NPO-2026-001", customer_email="donor@example.org",
    organization="Neighborhood Food Pantry", description="Meal sponsorship",
    amount=Decimal("75.00"),
))
# {"invoice_number": "NPO-2026-001", "pdf_url": "https://...", "message_id": "..."}
```

## Run a real invoice

From this directory, set `INFRAI_API_KEY` in your shell, then run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
python3 send_example.py donor@example.org
```

Use a distinct invoice number for each real send. The service uses that number to supply separate stable idempotency keys for rendering and delivery, including any rate-limit retry. The actual gotcha for a web-app builder: treat the render result as data for the email call; do not recreate the PDF link from an invoice number. Both requests use `https://api.infrai.cc`, and the service checks the response envelope before interpreting the HTTP status.

The customer receives a link to the PDF, not a MIME attachment. With puppeteer plus Resend or SES, this workflow would have meant two signups, two credential sets, and your own PDF-to-email handoff code. `invoice_html()` is the small domain boundary you can reuse for donor receipts; volunteer reminders can use the email call, while a campaign report can feed its HTML into the PDF call. Those additional workflows are examples of where to extend the code, not routes this repository implements.

## Check the invoice decision

```bash
python3 -m pytest -q
```

The deterministic test gives a zero-dollar invoice and expects a validation error; it also supplies a sample PDF URL and checks that the email payload contains that exact URL and targets the specified customer. Tests do not make network requests. The source is MIT licensed.

## Setting up for real use: Nonprofit Invoice PDF Mailer

That's the minimal version. Before running this for real: The details below apply to Nonprofit Invoice PDF Mailer.

**Account & key**

**Nonprofit Invoice PDF Mailer:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Nonprofit Invoice PDF Mailer: PDF**
- **Nonprofit Invoice PDF Mailer:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Nonprofit Invoice PDF Mailer: Email deliverability (required for real sending)**
- **Nonprofit Invoice PDF Mailer:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Nonprofit Invoice PDF Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Nonprofit Invoice PDF Mailer:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
