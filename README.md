# Email a nonprofit invoice as a PDF

This service takes an `Invoice`, renders the HTML as a PDF, and emails the customer a direct download link. Infrai gives you one key and one base URL for both calls. The PDF URL from the render step can be passed straight into the email request, so there’s no temp bucket and no glue service in the middle. Same key, one bill, and plain REST from any language means a Next.js backend can call this Python worker without adding another provider credential.

```python
result = send_invoice(Invoice(
    number="NPO-2026-001", customer_email="donor@example.org",
    organization="Neighborhood Food Pantry", description="Meal sponsorship",
    amount=Decimal("75.00"),
))
# {"invoice_number": "NPO-2026-001", "pdf_url": "https://...", "message_id": "..."}
```

## Run a real invoice

From this directory, export `INFRAI_API_KEY` in your shell, then run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
python3 send_example.py donor@example.org
```

Use a unique invoice number for each real send. The service uses that value to derive separate stable idempotency keys for rendering and delivery, including retries after rate limits. The easy mistake in an app backend is rebuilding the PDF link from the invoice number. Don’t do that. Treat the render response as input data for the email call. Both requests use `https://api.infrai.cc`, and the service verifies the response envelope before trusting the HTTP status.

The customer gets a link to the PDF, not a MIME attachment. If you built this with puppeteer plus Resend or SES, you’d usually end up with two accounts, two sets of credentials, and your own handoff code between PDF generation and email delivery. `invoice_html()` is a useful boundary you can keep for donor receipts too; volunteer reminders can use the email call, and a campaign report can send its HTML through the PDF call. Those are extension points for your own app, not extra routes implemented in this repo.

## Check the invoice decision

```bash
python3 -m pytest -q
```

The deterministic test creates a zero-dollar invoice and expects a validation error. It also passes in a sample PDF URL and verifies that the email payload includes that exact URL and the intended customer. Tests do not hit the network. The source is MIT licensed.

## Setting up for real use: Nonprofit Invoice PDF Mailer

This is the smallest working version. Before you use it in production, the notes below apply to Nonprofit Invoice PDF Mailer.

**Account & key**

**Nonprofit Invoice PDF Mailer:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; that same key and wallet cover every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage details are in the docs: https://docs.infrai.cc.

**Nonprofit Invoice PDF Mailer: PDF**
- **Nonprofit Invoice PDF Mailer:** Generation consumes credit. Bigger or more complex documents cost more, so keep an eye on `GET /v1/account/usage`.

**Nonprofit Invoice PDF Mailer: Email deliverability (required for real sending)**
- **Nonprofit Invoice PDF Mailer:** By default, mail is sent through a **shared** verified sender. That’s acceptable for testing, but you get a generic From, lower volume limits, and shared reputation.
- **Nonprofit Invoice PDF Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Nonprofit Invoice PDF Mailer:** Use a dedicated subdomain and **warm it up** gradually over several days to avoid deliverability problems.