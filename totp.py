import pyotp
import os
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from email.mime.image import MIMEImage
import smime
import qrcode

basedir = os.path.abspath(os.path.dirname(__file__))

def sendMail(to:string):
    otp=pyotp.TOTP('base32secret3232').provisioning_uri(name='admin@cytech.eu', issuer_name='CY Diploma')
    qr = qrcode.make(otp)
    qr.save("assets/qrcode.png")
    otp=pyotp.TOTP('base32secret3232')
    msg = MIMEMultipart()
    msg['From'] = 'cyu.otpdiploma@gmail.com'
    msg['To'] = to
    msg['Subject'] = 'Your OTP QRCODE'
    with open("assets/qrcode.png", 'rb') as f:
        img_data = f.read()
    image = MIMEImage(img_data, name="OTP.png")
    msg.attach(image)
    s = smtplib.SMTP("smtp.gmail.com",587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login('cyu.otpdiploma@gmail.com', 'admincyuniversite')
    s.sendmail(to, to, msg.as_string())
    s.quit()
    return otp

def verifyotp(token):
    otp=pyotp.TOTP('base32secret3232')
    return otp.verify(token)

def maildiploma(diploma,to):
    #La partie commenté correspond à l'envoie en format smime, cependant le destinataire doit possédé la signature, sinon le mail est illisilbe
    with open(diploma, 'rb') as f:
        img_data = f.read()
    message = MIMEMultipart()
    message['From'] = "cyu.otpdiploma@gmail.com"
    message['To'] = to
    message['Subject'] = "Your diploma"
    image = MIMEImage(img_data, name="Diploma.png")
    message.attach(image)
    #with open('cert/cert.pem', 'rb') as pem:
        #message = smime.encrypt('\n'.join(message), pem.read())
    s = smtplib.SMTP("smtp.gmail.com",587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login('cyu.otpdiploma@gmail.com', 'admincyuniversite')
    s.sendmail(to, to, message.as_string())
    #s.sendmail(to, to, message)
    s.quit()

