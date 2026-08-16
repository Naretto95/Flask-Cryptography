# Flask-Cryptography

A Flask web application for issuing tamper-evident digital diplomas for a
school. A student requests a diploma, an admin approves it behind a TOTP
one-time-password check, and the app generates a unique diploma image that
is both digitally signed and watermarked — so any copy of it can later be
verified by re-uploading it to the site.

## How a diploma is protected

Each approved diploma goes through two independent layers of protection,
applied to the same source image:

1. **RSA-signed QR code** — the diploma's data (name, school,
   specialization, graduation year, timestamp) is encrypted with the
   server's RSA key and encoded into a QR code printed on the diploma.
   Verifying a diploma decrypts and reads back that data with the matching
   key (see `src/crypt_function.py`).
2. **LSB steganography watermark** — the same data is additionally hidden
   in the least-significant bits of the image's pixels, invisible to the
   eye, as a second, independent check (see `src/stegano.py`).

Uploading a diploma image on the home page runs both checks and reports
what each one recovered.

## Features
- Student registration/login and diploma requests
- Admin panel to review pending requests, gated by a TOTP one-time password
  emailed to the admin as a QR code
- Approved diplomas are signed, watermarked, and emailed to the student
- Public certificate verification: upload any diploma image and recover its
  embedded data
- Refusing a pending request (there is no "revoke" of an already-issued
  diploma — verification is meant to be permanent)

## Getting started

Requires Python 3.11+ and pip.

1. Clone the repository:
   ```
   git clone https://github.com/Naretto95/Flask-Cryptography.git
   cd Flask-Cryptography
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure environment variables — copy `.env.example` to `.env` and fill
   it in:
   ```
   cp .env.example .env
   ```
   - `SECRET_KEY` — Flask session signing key. Generate one with
     `python -c "import secrets; print(secrets.token_hex(32))"`.
   - `EMAIL_FROM` / `EMAIL_PASSWORD` / `SMTP_SERVER` / `SMTP_PORT` — SMTP
     account used to send the admin's OTP QR code and finished diplomas.
     Without real values, the app still runs but those emails will fail to
     send.
   - `TOTP_SECRET` — shared seed for the admin's one-time password.
   - `RSA_KEY_PASSPHRASE` — passphrase protecting
     `ressources/private/key.pem`.
   - `DATABASE_URL`, `FLASK_DEBUG`, `FLASK_PORT` — optional, sensible
     defaults are used if omitted.
4. Start the application:
   ```
   python app.py
   ```
5. Visit [http://localhost:8000](http://localhost:8000).

## Contribution
We are open to contributions and suggestions. If you would like to
contribute, please fork the repository and create a pull request with your
changes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Acknowledgements
This project makes use of the Flask web framework, and various other Python
libraries for cryptography, QR codes, and image processing.
