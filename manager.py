from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import login_user,LoginManager
from flask_cors import CORS
import os

app = Flask(__name__)
cors = CORS(app,resources={
  r'/*': {
    "origins":"*"
  }
  })

SEND_FOLDER = 'ressources'+os.path.sep+'Diplomas'
UPLOAD_FOLDER = 'ressources'+os.path.sep+'DL_Diplomas'
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
def load_user(user):
    return User.query.get(user)

class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column('id',db.Integer,primary_key = True)
    name = db.Column('name',db.String(50))
    first_name = db.Column('first_name',db.String(50))
    password =db.Column('password',db.String(255))
    mail = db.Column('mail',db.String(255))
    admin = db.Column('admin',db.Integer)
    school = db.Column("school",db.String(255))

    def __init__(self,name,first_name,password,mail,school,admin):
        self.name = name
        self.first_name = first_name
        self.password = password
        self.mail = mail
        self.admin = admin
        self.school = school

class Diploma(db.Model) :
    __tablename__ = 'diploma'
    _id = db.Column('id',db.Integer,primary_key = True)
    _id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_link = db.relationship("User")
    graduation_years = db.Column("graduation_years",db.String(8))
    specialisation =db.Column("specialisation",db.String(255))
    status = db.Column('status',db.Integer)# 0 : validé 1:refusé 2: en attente
    hash =db.Column('hash',db.String(255))

    def __init__(self,_id_user,graduation_years,specialisation,status): 
        self._id_user = _id_user
        self.graduation_years = graduation_years
        self.specialisation = specialisation
        self.status = status

    def set_hash(self,hash):
        self.hash = hash

    def get_hash(self):
        return self.hash

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','name','first_name','password','mail','admin','school')

class DiplomaSchema(ma.Schema) : 
    class Meta:
        fields =('id','_id_user','graduation_years','specialisation','status')

def save_user(user):    
    new_user = User(user['name'],user["first_name"],user['password'],user['email'],user['school'],False)  
    db.session.add(new_user)
    db.session.commit()

def all_diplomas():
     return Diploma.query.all()

def save_diploma(diploma):
    new_diploma=Diploma(diploma['id_user'],diploma['graduation_years'],diploma['specialisation'],diploma['status'])
    db.session.add(new_diploma)
    db.session.commit()

def search_user(id_user) : 
    return User.query.filter_by(id = id_user).first()

def checksum(mail, password) :
    user = User.query.filter_by(mail = mail).first() 
    if user != None : 
        if password == user.password : 
            login_user(user)
            return (True,user.id)
        else : 
            return (False,0)
    else :
        return (False,0)

def check_user(mail):
    if User.query.filter_by(mail = mail).first() :
        return False 
    else:
        return True

def check_admin(mail):
    usr = User.query.filter_by(mail = mail).first()
    return usr.admin 

def user_diploma(user_id):
    diplomas = []
    query_di = Diploma.query.filter_by(_id_user = user_id)
    for elem in query_di:
        diplomas.append(elem)
    return diplomas

def make_diploma(diploma_id):
    data = ''
    try :
        diploma = Diploma.query.filter_by( _id= diploma_id).first()
        user = User.query.filter_by(_id_user = diploma._user_id)
        data+=user.first_name+","+user.name+","+user.school+","+diploma.specialisation+","+diploma.graduation_years
    except:
        print("This diploma is not registered")
    
    