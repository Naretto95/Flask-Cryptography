import os 
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import qrcode
from PIL import Image,ImageDraw,ImageFont
from shutil import copyfile
from src.stegano import *
from pyzbar import pyzbar
import time
from asn1crypto import tsp

path_parent = os.path.dirname(os.getcwd())

def encrypt_private_key(a_message, private_key):
    encryptor = PKCS1_OAEP.new(private_key)
    encrypted_msg = encryptor.encrypt(a_message.encode())
    encoded_encrypted_msg = base64.b64encode(encrypted_msg)
    return encoded_encrypted_msg

def verifie(encrypt_message):
    with open(os.getcwd()+os.path.sep+'private'+os.path.sep+'key.pem','r') as f :
        private_keys = RSA.importKey(f.read(),passphrase="keepbreathing")
    return decrypt_public_key(encrypt_message,private_keys)
    
def decrypt_public_key(encoded_encrypted_msg, public_key):
    encryptor = PKCS1_OAEP.new(public_key)
    decoded_encrypted_msg = base64.b64decode(encoded_encrypted_msg)
    decoded_decrypted_msg = encryptor.decrypt(decoded_encrypted_msg)
    return decoded_decrypted_msg

def sign(token):   
    with open(os.getcwd()+os.path.sep+"cert"+os.path.sep+"cert.pem","r") as certif:
        public_key = RSA.importKey(certif.read())
    return encrypt_private_key(token,public_key)
    
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
    diploma.save(os.getcwd()+os.path.sep+"Diplomas"+os.path.sep+"diploma_"+str(id_diploma)+'.png')

def generate_unique_diploma(user,diploma):
    """print Name, diploma and years on diploma and make some steganography to 
    transform standard picture to a unique one"""
    copyfile(os.getcwd()+os.path.sep+"assets"+os.path.sep+"empty_diploma.png","temp.png")
    img = Image.open('temp.png')
    ts = str(time.time())
    #ts = timeStamp('temp.png')
    #ts = ts[:ts.find('b"')]
    #ts = ts.replace("<asn1crypto.core.OctetString ","")
    secret_data= user.first_name+user.name+diploma.specialisation+user.school+str(diploma.graduation_years)+ts
    ls =len(secret_data)
    if  ls < 64 :
        for i in range(64-ls):
            secret_data+='.'
    empty_dip =  Image.open("temp.png")
    d = ImageDraw.Draw(empty_dip)
    fnt = ImageFont.truetype(os.getcwd()+os.path.sep+'assets'+os.path.sep+'AlgerianRegular.ttf', 50)
    pos_user = ((empty_dip.size[0]//2-200,empty_dip.size[1]//2-100))
    pos_diploma=((empty_dip.size[0]//2-200,empty_dip.size[1]//2-50))
    pos_years = ((empty_dip.size[0]//2-100,empty_dip.size[1]//2))
    user_draw  = user.first_name +' '+user.name
    diploma_draw = diploma.specialisation +' '+user.school
    d.text(pos_user,user_draw,fill=(0,0,0),font=fnt)
    d.text(pos_diploma,diploma_draw,fill=(0,0,0),font=fnt)
    d.text(pos_years,str(diploma.graduation_years),fill=(0,0,0),font=fnt)
    empty_dip.save("ready_to_qr.png")
    print('drawing done')
    generate_qrcode(secret_data,'ready_to_qr.png',diploma._id)
    img=Image.open(os.getcwd()+os.path.sep+"Diplomas"+os.path.sep+"diploma_"+str(diploma._id)+'.png')
    cacher(img,secret_data)
    img.save("Diplomas"+os.path.sep+"diploma_"+str(diploma._id)+'.png')
    print('diploma_generated')
    #cleaning temp file 
    os.remove("temp.png")
    os.remove("ready_to_qr.png")
    os.remove('qr_temp.png')
    print('cleaning done')

def decrypt_img(filename):
    diploma   = Image.open(filename)
    qr = pyzbar.decode(diploma)
    encryp_me = qr[0].data.decode()
    return [verifie(encryp_me).decode(),recuperer(diploma,64)]

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
    print(signed_attrs)  
    return str(signature)

