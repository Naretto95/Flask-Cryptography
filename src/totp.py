import pyotp
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import qrcode

# Constants
TOTP_SECRET = 'base32secret3232'
EMAIL_FROM = 'cyu.otpdiploma@gmail.com'
EMAIL_PASSWORD = 'admincyuniversite'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
QR_PATH = os.path.join('ressources', 'assets', 'qrcode.png')

def sendMail(to: str):
    otp_uri = pyotp.TOTP(TOTP_SECRET).provisioning_uri(name='admin@cytech.eu', issuer_name='CY Diploma')
    qr = qrcode.make(otp_uri)
    qr.save(os.path.join(os.getcwd(), QR_PATH))
    otp = pyotp.TOTP(TOTP_SECRET)
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to
    msg['Subject'] = 'Your OTP QRCODE'
    with open(os.path.join(os.getcwd(), QR_PATH), 'rb') as f:
        img_data = f.read()
    image = MIMEImage(img_data, name="OTP.png")
    msg.attach(image)
    try:
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(EMAIL_FROM, EMAIL_PASSWORD)
        s.sendmail(EMAIL_FROM, to, msg.as_string())
        s.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
    return otp

def verifyotp(token: str) -> bool:
    otp = pyotp.TOTP(TOTP_SECRET)
    return otp.verify(token)

def maildiploma(diploma: str, to: str):
    with open(diploma, 'rb') as f:
        img_data = f.read()
    message = MIMEMultipart()
    message['From'] = EMAIL_FROM
    message['To'] = to
    message['Subject'] = "Your diploma"
    image = MIMEImage(img_data, name="Diploma.png")
    message.attach(image)
    try:
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(EMAIL_FROM, EMAIL_PASSWORD)
        s.sendmail(EMAIL_FROM, to, message.as_string())
        s.quit()
    except Exception as e:
        print(f"Error sending diploma email: {e}")

