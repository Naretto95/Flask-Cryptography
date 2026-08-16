import os
import base64
import tempfile
import time
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
import qrcode
from PIL import Image, ImageDraw, ImageFont
from shutil import copyfile
from src.stegano import *
from pyzbar import pyzbar

# Path constants
CERT_PATH = os.path.join('ressources', 'cert', 'cert.pem')
PRIVATE_KEY_PATH = os.path.join('ressources', 'private', 'key.pem')
DIPLOMAS_DIR = os.path.join('ressources', 'Diplomas')
ASSETS_DIR = os.path.join('ressources', 'assets')
EMPTY_DIPLOMA_PATH = os.path.join(ASSETS_DIR, 'empty_diploma.png')
FONT_PATH = os.path.join(ASSETS_DIR, 'AlgerianRegular.ttf')

RSA_KEY_PASSPHRASE = os.environ.get('RSA_KEY_PASSPHRASE', 'keepbreathing')


def sign(data: str) -> str:
    """Sign `data` with the issuer's private key. Only the server, which
    holds that key, can produce a valid signature -- this is what makes a
    diploma unforgeable."""
    with open(os.path.join(os.getcwd(), PRIVATE_KEY_PATH), 'r') as f:
        private_key = RSA.importKey(f.read(), passphrase=RSA_KEY_PASSPHRASE)
    digest = SHA256.new(data.encode())
    signature = pss.new(private_key).sign(digest)
    return base64.b64encode(signature).decode()

def verify(data: str, signature_b64: str) -> bool:
    """Check that `signature_b64` is a valid signature of `data`, using the
    issuer's public certificate. This only needs the public certificate, so
    anyone -- including this public verification page -- can run it without
    ever touching the private key."""
    with open(os.path.join(os.getcwd(), CERT_PATH), "r") as certif:
        public_key = RSA.importKey(certif.read())
    digest = SHA256.new(data.encode())
    try:
        pss.new(public_key).verify(digest, base64.b64decode(signature_b64))
        return True
    except (ValueError, TypeError):
        return False

def generate_qrcode(secret_data, path, id_diploma, tmpdir):
    # The QR carries the signature alongside the plaintext data: a
    # signature only proves who produced the data, it doesn't hide or
    # recover it. Split once from the left so the data half may safely
    # contain any character (base64 signatures never contain ':').
    signature_b64 = sign(secret_data)
    token = f"{signature_b64}:{secret_data}"
    qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_temp_path = os.path.join(tmpdir, "qr_temp.png")
    img_qr.save(qr_temp_path)
    diploma = Image.open(path)
    img_qr = Image.open(qr_temp_path)
    img_qr.thumbnail((350,350))
    qr_pos = (diploma.size[0]-360,diploma.size[1]-360)
    diploma.paste(img_qr,qr_pos)
    diploma.save(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{id_diploma}.png"))

def draw_centered_text(draw, center_x, y, text, font, fill=(0, 0, 0)):
    """Draw `text` horizontally centered on `center_x`, measuring its actual
    rendered width instead of guessing -- a fixed-offset guess drifts off
    center for any text shorter or longer than whatever length it was
    tuned for."""
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    draw.text((center_x - text_width / 2 - left, y), text, fill=fill, font=font)

def generate_unique_diploma(user, diploma):
    """print Name, diploma and years on diploma and make some steganography to
    transform standard picture to a unique one"""

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = os.path.join(tmpdir, "temp.png")
        ready_to_qr_path = os.path.join(tmpdir, "ready_to_qr.png")

        copyfile(os.path.join(os.getcwd(), EMPTY_DIPLOMA_PATH), temp_path)
        ts = str(time.time())
        secret_data = user.first_name + user.name + diploma.specialization + user.school + str(diploma.graduation_year) + ts
        secret_data = secret_data + '.' * (64 - len(secret_data))
        empty_dip = Image.open(temp_path)
        d = ImageDraw.Draw(empty_dip)
        fnt = ImageFont.truetype(os.path.join(os.getcwd(), FONT_PATH), 50)
        center_x = empty_dip.size[0] // 2
        center_y = empty_dip.size[1] // 2
        user_draw = user.first_name + ' ' + user.name
        diploma_draw = diploma.specialization + ' ' + user.school
        draw_centered_text(d, center_x, center_y - 100, user_draw, fnt)
        draw_centered_text(d, center_x, center_y - 50, diploma_draw, fnt)
        draw_centered_text(d, center_x, center_y, str(diploma.graduation_year), fnt)
        empty_dip.save(ready_to_qr_path)
        generate_qrcode(secret_data, ready_to_qr_path, diploma.id, tmpdir)
        img = Image.open(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))
        cacher(img, secret_data)
        img.save(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))

class InvalidCertificate(Exception):
    """Raised when an uploaded certificate has no QR code, or its
    signature doesn't check out against the issuer's public certificate."""

def decrypt_img(filename):
    try:
        diploma = Image.open(filename)
        qr_codes = pyzbar.decode(diploma)
    except OSError:
        raise InvalidCertificate("This file isn't a readable image.")
    if not qr_codes:
        raise InvalidCertificate("No QR code found on this certificate.")
    signature_b64, _, data = qr_codes[0].data.decode().partition(':')
    if not verify(data, signature_b64):
        raise InvalidCertificate("Signature does not match: this certificate is invalid or has been tampered with.")
    return [data, recuperer(diploma, 64)]
