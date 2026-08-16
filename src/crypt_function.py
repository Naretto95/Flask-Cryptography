import os
import base64
import tempfile
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
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


def encrypt_private_key(a_message, private_key):
    encryptor = PKCS1_OAEP.new(private_key)
    encrypted_msg = encryptor.encrypt(a_message.encode())
    encoded_encrypted_msg = base64.b64encode(encrypted_msg)
    return encoded_encrypted_msg

def decrypt_public_key(encoded_encrypted_msg, public_key):
    encryptor = PKCS1_OAEP.new(public_key)
    decoded_encrypted_msg = base64.b64decode(encoded_encrypted_msg)
    decoded_decrypted_msg = encryptor.decrypt(decoded_encrypted_msg)
    return decoded_decrypted_msg

def sign(token):
    with open(os.path.join(os.getcwd(), CERT_PATH), "r") as certif:
        public_key = RSA.importKey(certif.read())
    return encrypt_private_key(token, public_key)

def verify(encrypt_message):
    with open(os.path.join(os.getcwd(), PRIVATE_KEY_PATH), 'r') as f:
        private_keys = RSA.importKey(f.read(), passphrase=RSA_KEY_PASSPHRASE)
    return decrypt_public_key(encrypt_message, private_keys)

def generate_qrcode(secret_data, path, id_diploma, tmpdir):
    token = sign(secret_data)
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
        pos_user = ((empty_dip.size[0]//2-200,empty_dip.size[1]//2-100))
        pos_diploma=((empty_dip.size[0]//2-200,empty_dip.size[1]//2-50))
        pos_years = ((empty_dip.size[0]//2-100,empty_dip.size[1]//2))
        user_draw  = user.first_name +' '+user.name
        diploma_draw = diploma.specialization +' '+user.school
        d.text(pos_user,user_draw,fill=(0,0,0),font=fnt)
        d.text(pos_diploma,diploma_draw,fill=(0,0,0),font=fnt)
        d.text(pos_years,str(diploma.graduation_year),fill=(0,0,0),font=fnt)
        empty_dip.save(ready_to_qr_path)
        generate_qrcode(secret_data, ready_to_qr_path, diploma.id, tmpdir)
        img = Image.open(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))
        cacher(img, secret_data)
        img.save(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))

def decrypt_img(filename):
    diploma   = Image.open(filename)
    qr = pyzbar.decode(diploma)
    encryp_me = qr[0].data.decode()
    return [verify(encryp_me).decode(),recuperer(diploma,64)]
