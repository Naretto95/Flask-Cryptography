import os
from flask import  render_template,request,session
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import redirect
from flask import send_file
import base64
from werkzeug.utils import secure_filename
from crypt_function import decrypt_img, generate_unique_diploma,verifie
from manager import *
from totp import sendMail,verifyotp,maildiploma

basedir = os.path.abspath(os.path.dirname(__file__))

user_schema = UserSchema()
users_schema = UserSchema( many=True )
diploma_schema = DiplomaSchema()
diplomas_schema = DiplomaSchema(many = True)


@app.route("/", methods=['GET', 'POST'])
def home():
    home=True
    if request.method == 'POST':
        try :
            file = request.files['file']
            name = secure_filename(file.filename)
            file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'],name))
            code = decrypt_img(os.path.join(basedir, app.config['UPLOAD_FOLDER'],name))
            success = "QRCODE : "+code[0]+" STENO : "+code[1]
            os.remove(os.path.join(basedir, app.config['UPLOAD_FOLDER'],name))
            return render_template('index.html',home=home,success=success)
        except :
            return render_template('index.html',home=home,warning = "File not found !")
    return render_template('index.html',home=home)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/login", methods=['POST','GET'])
def login():
    login=True
    if current_user.is_authenticated:
        return render_template('/')
    elif request.method == 'POST':
        mail = request.form['email']
        password = request.form['password']
        check = checksum(mail,password)
        if check[0] and check_admin(mail):      
            return redirect('/admin')
        elif check[0] and check_admin(mail) == False:
            return redirect('/diplomas')
        else: 
            return render_template('login.html',login=login,warning="Incorrect password/email combination !")
    else:
        return render_template('login.html',login=login)

@app.route("/register",methods=['POST','GET'])
def register():
    register=True
    if current_user.is_authenticated:
        return render_template('/')
    elif request.method == 'POST':      
        if check_user(request.form['email']):
            user = {}
            user['email'] = request.form['email']
            user['name'] = request.form['lname']
            user['first_name'] = request.form['fname']
            user['password'] = request.form['password']
            if request.form['school'] in ["CYTECH","EISTI"]:
                user['school'] = request.form['school']
            else:
                user['school'] = "CYTECH"
            save_user(user)
            check = checksum(user['email'],user['password'])
            if check[0] and check_admin(user['email']):      
                return redirect('/admin')
            elif check[0] and check_admin(user['email']) == False:
                return redirect('/diplomas')
            else: 
                return render_template('login.html',login=login)
        else:
            return render_template('register.html',register=register,warning="This mail already exists !")
    else : 
        return render_template('register.html',register=register)

@app.route("/diplomas",methods=['POST','GET'])
@login_required
def diploma():
    diploma=True
    if current_user.admin:
        return redirect('/admin')
    tab_diploma = user_diploma(current_user.id)
    if request.method == 'POST':
        if "certif" in request.form:        
            diploma = {}
            diploma['id_user'] = current_user.id
            diploma['specialisation'] = request.form['specialisation']
            diploma['graduation_years'] = request.form['graduation_years']
            diploma['status'] = 2 
            save_diploma(diploma)
            tab_diploma.append(diploma)
            return render_template('/user.html',diplomas = tab_diploma, n = len(tab_diploma),diploma=diploma,success="Diploma verification sent !")
        elif "download" in request.form:
            diplomaid = request.form["download"]
            diploma = Diploma.query.get(diplomaid)
            if diploma._id_user == current_user.id:
                return send_file(os.path.join(basedir, app.config['SEND_FOLDER'],'diploma_'+str(diploma._id)+".png"), as_attachment=True)
            else:
                return render_template('/user.html',diplomas = tab_diploma,n = len(tab_diploma),diploma=diploma,warning = "Error !")
        elif "mail" in request.form:
            diplomaid = request.form["mail"]
            diploma = Diploma.query.get(diplomaid)
            maildiploma(os.path.join(basedir, app.config['SEND_FOLDER'],'diploma_'+str(diploma._id)+".png"),current_user.mail)
            return render_template('/user.html',diplomas = tab_diploma,n = len(tab_diploma),diploma=diploma,success="Mail sent to "+current_user.mail+" !")
    else:
        return render_template('/user.html',diplomas = tab_diploma,n = len(tab_diploma),diploma=diploma)
        
@app.route("/admin",methods=['POST','GET'])
@login_required
def admin():
    admin=True
    warning = None
    success = None
    if not current_user.admin:
        return redirect('/')
    else:
        if request.method == 'POST':
            if "otp" in request.form:
                otpverif = request.form["otpverif"]
                otp = request.form["otp"]
                if verifyotp(otpverif):
                    diploma = Diploma.query.get(otp)
                    diploma.status=1
                    user = User.query.get(diploma._id_user)
                    make_diploma(diploma._id)
                    generate_unique_diploma(user,diploma)
                    success = "Diploma validated !"
                    maildiploma(os.path.join(basedir, app.config['SEND_FOLDER'],'diploma_'+str(diploma._id)+".png"),user.mail)
                else : 
                    warning = "Wrong OTP !"
            elif "refuse" in request.form:
                refuse = request.form["refuse"]
                diploma = Diploma.query.get(refuse)
                diploma.status=0
                warning = "Diploma refused !"
        db.session.commit()
        tab_diploma = all_diplomas()
        diploma_users=[]
        for diploma in tab_diploma : 
            diploma_users.append(search_user(diploma._id_user))            
        return render_template('admin.html',diplomas=tab_diploma, n = len(tab_diploma),admin=admin,warning=warning,success=success)

@app.route("/otp/<mail>",methods=['POST','GET'])
@login_required
def otp(mail):
    if mail==current_user.mail and current_user.admin:
        sendMail(mail)
        return "OTP Sent !"


if __name__ == '__main__' :
    db.create_all()
    app.run(debug=True,port = 8000)
