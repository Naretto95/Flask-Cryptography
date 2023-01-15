from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import login_user,LoginManager
from flask_cors import CORS
import os

app = Flask(__name__)
cors = CORS(app, resources={r'/*': {"origins":"*"}})

SEND_FOLDER = os.path.join('ressources', 'Diplomas')
UPLOAD_FOLDER = os.path.join('ressources', 'DL_Diplomas')
app.config['SEND_FOLDER'] = SEND_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "Keep breathing. That's the key.Breathe "
app.config['CORS_HEADERS'] = 'Content-Type'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
ma = Marshmallow(app)

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
    status = db.Column(db.Integer)  # 0: validated, 1: rejected, 2: pending
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

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'first_name', 'password', 'email', 'is_admin', 'school')

class DiplomaSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'graduation_year', 'specialization', 'status')

def save_user(user):
    new_user = User(user['name'],user["first_name"],user['password'],user['email'],user['school'],False)
    db.session.add(new_user)
    db.session.commit()

def all_diplomas():
    return Diploma.query.all()

def save_diploma(diploma):
    new_diploma = Diploma(diploma['id_user'],diploma['graduation_years'],diploma['specialisation'],diploma['status'])
    db.session.add(new_diploma)
    db.session.commit()

def search_user(id_user):
    return User.query.filter_by(id=id_user).first()

def checksum(mail, password):
    user = User.query.filter_by(mail=mail).first()
    if user:
        if password == user.password:
            login_user(user)
            return (True, user.id)
        else:
            return (False, 0)
    else:
        return (False, 0)

def check_user(mail):
    return not bool(User.query.filter_by(mail=mail).first())

def check_admin(mail):
    return User.query.filter_by(mail=mail, admin=True).first() is not None

def user_diploma(user_id):
    return Diploma.query.filter_by(user_id=user_id).all()

def make_diploma(diploma_id):
    diploma = Diploma.query.filter_by(id=diploma_id).first()
    if not diploma:
        print("This diploma is not registered")
        return
    
    user = User.query.filter_by(id=diploma.user_id).first()
    data = f"{user.first_name},{user.name},{user.school},{diploma.specialisation},{diploma.graduation_years}"
    return data
    
    