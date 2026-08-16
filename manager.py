from flask import Flask
from flask_login import UserMixin, login_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SEND_FOLDER = os.path.join('ressources', 'Diplomas')
UPLOAD_FOLDER = os.path.join('ressources', 'DL_Diplomas')
app.config['SEND_FOLDER'] = SEND_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///crypto_db.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-insecure-key-change-me')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    password = db.Column(db.String(255))
    mail = db.Column(db.String(255))
    admin = db.Column(db.Integer)
    school = db.Column(db.String(255))

    def __init__(self, name, first_name, password, mail, school, admin):
        self.name = name
        self.first_name = first_name
        self.password = password
        self.mail = mail
        self.admin = admin
        self.school = school

class Diploma(db.Model):
    __tablename__ = 'diplomas'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User")
    graduation_year = db.Column(db.String(8))
    specialization = db.Column(db.String(255))
    status = db.Column(db.Integer)  # 0: refused, 1: approved, 2: pending
    hash = db.Column(db.String(255))

    def __init__(self, user_id, graduation_year, specialization, status):
        self.user_id = user_id
        self.graduation_year = graduation_year
        self.specialization = specialization
        self.status = status

    def set_hash(self, hash_value):
        self.hash = hash_value

    def get_hash(self):
        return self.hash

def save_user(user):
    hashed_password = generate_password_hash(user['password'])
    new_user = User(user['name'],user["first_name"],hashed_password,user['email'],user['school'],False)
    db.session.add(new_user)
    db.session.commit()

def all_diplomas():
    return Diploma.query.all()

def save_diploma(diploma):
    new_diploma = Diploma(diploma['user_id'], diploma['graduation_year'], diploma['specialization'], diploma['status'])
    db.session.add(new_diploma)
    db.session.commit()

def authenticate(mail, password):
    """Checks credentials and, on success, logs the user in (flask_login side effect)."""
    user = User.query.filter_by(mail=mail).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return (True, user.id)
    else:
        return (False, 0)

def is_email_available(mail):
    return not bool(User.query.filter_by(mail=mail).first())

def check_admin(mail):
    return User.query.filter_by(mail=mail, admin=True).first() is not None

def user_diploma(user_id):
    return Diploma.query.filter_by(user_id=user_id).all()


def create_sample_users():
    admin_data = {
        'email': 'admin@example.com',
        'name': 'Admin',
        'first_name': 'Super',
        'password': 'adminpass',
        'school': 'CYTECH'
    }
    save_user(admin_data)
    admin_user = User.query.filter_by(mail='admin@example.com').first()
    admin_user.admin = True
    db.session.commit()

    user_data = {
        'email': 'user@example.com',
        'name': 'User',
        'first_name': 'Normal',
        'password': 'userpass',
        'school': 'CYTECH'
    }
    save_user(user_data)
