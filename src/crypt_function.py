import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import qrcode
from PIL import Image, ImageDraw, ImageFont
from shutil import copyfile
from src.stegano import *
from pyzbar import pyzbar
import time
from asn1crypto import tsp

# Path constants
CERT_PATH = os.path.join('ressources', 'cert', 'cert.pem')
PRIVATE_KEY_PATH = os.path.join('ressources', 'private', 'key.pem')
DIPLOMAS_DIR = os.path.join('ressources', 'Diplomas')
ASSETS_DIR = os.path.join('ressources', 'assets')
EMPTY_DIPLOMA_PATH = os.path.join(ASSETS_DIR, 'empty_diploma.png')
FONT_PATH = os.path.join(ASSETS_DIR, 'AlgerianRegular.ttf')


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
        private_keys = RSA.importKey(f.read(), passphrase="keepbreathing")
    return decrypt_public_key(encrypt_message, private_keys)

def generate_qrcode(secret_data, path,id_diploma):
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
    img_qr.save("qr_temp.png")    
    diploma = Image.open(path)
    img_qr = Image.open("qr_temp.png")
    img_qr.thumbnail((350,350))
    qr_pos = (diploma.size[0]-360,diploma.size[1]-360)
    diploma.paste(img_qr,qr_pos)
    diploma.save(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{id_diploma}.png"))

def generate_unique_diploma(user, diploma):
    """print Name, diploma and years on diploma and make some steganography to 
    transform standard picture to a unique one"""

    copyfile(os.path.join(os.getcwd(), EMPTY_DIPLOMA_PATH), "temp.png")
    img = Image.open('temp.png')
    ts = str(time.time())
    secret_data = user.first_name + user.name + diploma.specialization + user.school + str(diploma.graduation_year) + ts
    secret_data = secret_data + '.' * (64 - len(secret_data))
    empty_dip = Image.open("temp.png")
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
    empty_dip.save("ready_to_qr.png")
    generate_qrcode(secret_data,'ready_to_qr.png',diploma.id)
    img = Image.open(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))
    cacher(img, secret_data)
    img.save(os.path.join(os.getcwd(), DIPLOMAS_DIR, f"diploma_{diploma.id}.png"))
    os.remove("temp.png")
    os.remove("ready_to_qr.png")
    os.remove('qr_temp.png')

def decrypt_img(filename):
    diploma   = Image.open(filename)
    qr = pyzbar.decode(diploma)
    encryp_me = qr[0].data.decode()
    return [verify(encryp_me).decode(),recuperer(diploma,64)]

def timeStamp(filename):
    os.system('openssl ts -query -data '+filename+' -no_nonce -sha512 -cert -out '+filename+'.tsq' ) 
    os.system('curl -H "Content-Type: application/timestamp-query" --data-binary '+'"@'+filename+'.tsq" '+'freetsa.org/tsr >'+filename+'.tsr')
    with open(filename+'.tsr', 'rb') as f :
        res = tsp.TimeStampResp.load(f.read())
    token = res['time_stamp_token']
    signed_data = token['content']
    signer_infos = signed_data['signer_infos']
    signer_info = signer_infos[0]
    signed_attrs = signer_info['signed_attrs']
    signature = signer_info['signature']
    return str(signature)

