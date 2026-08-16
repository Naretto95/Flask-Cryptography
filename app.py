import os
import uuid
from flask import render_template, request, url_for, send_file
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import redirect, secure_filename
from src.crypt_function import decrypt_img, generate_unique_diploma
from manager import *
from src.totp import sendMail,verifyotp,maildiploma

basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Empty directories aren't tracked by git, so make sure the folders the app
# writes uploads/diplomas into actually exist on a fresh checkout.
os.makedirs(os.path.join(basedir, app.config['UPLOAD_FOLDER']), exist_ok=True)
os.makedirs(os.path.join(basedir, app.config['SEND_FOLDER']), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET', 'POST'])
def home():
    home = True
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file_path = os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            code = decrypt_img(file_path)
            os.remove(file_path)
            return render_template('Index.html', home=home, success=f"QRCODE : {code[0]} STENO : {code[1]}")
        else:
            return render_template('Index.html', home=home, warning="File not found / Wrong type of file !")
    return render_template('Index.html', home=home)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/login", methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        mail = request.form['email']
        password = request.form['password']
        check = authenticate(mail,password)
        if check[0]:
            if check_admin(mail):
                return redirect('/admin')
            else:
                return redirect('/diplomas')
        else:
            return render_template('Login.html', warning="Incorrect password/email combination !")
    return render_template('Login.html', login=True)

@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    elif request.method == 'POST':
        email = request.form['email']
        if is_email_available(email):
            user = {
                'email': email,
                'name': request.form['lname'],
                'first_name': request.form['fname'],
                'password': request.form['password'],
                'school': request.form['school'] if request.form['school'] in ["CYTECH", "EISTI"] else "CYTECH"
            }
            save_user(user)
            check = authenticate(user['email'], user['password'])
            if check[0] and check_admin(user['email']):
                return redirect('/admin')
            else:
                return redirect('/diplomas')
        else:
            return render_template('Register.html', register=True, warning="This email already exists!")
    else:
        return render_template('Register.html', register=True)

@app.route("/diplomas", methods=['POST', 'GET'])
@login_required
def diploma():
    diploma = True
    if check_admin(current_user.mail):
        return redirect('/admin')
    tab_diploma = user_diploma(current_user.id)

    if request.method == 'POST':
        if "certif" in request.form:
            diploma = {}
            diploma['user_id'] = current_user.id
            diploma['specialization'] = request.form['specialization']
            diploma['graduation_year'] = request.form['graduation_year']
            diploma['status'] = 2
            save_diploma(diploma)
            tab_diploma.append(diploma)
            return render_template('/User.html', diplomas=tab_diploma, n=len(tab_diploma), diploma=diploma, success="Diploma verification sent!")

        elif "download" in request.form:
            diplomaid = request.form["download"]
            diploma = Diploma.query.get(diplomaid)
            if diploma and diploma.user_id == current_user.id:
                return send_file(os.path.join(basedir, app.config['SEND_FOLDER'], 'diploma_'+str(diploma.id)+".png"), as_attachment=True)
            else:
                return render_template('/User.html', diplomas=tab_diploma, n=len(tab_diploma), diploma=diploma, warning="Error!")

        elif "mail" in request.form:
            diplomaid = request.form["mail"]
            diploma = Diploma.query.get(diplomaid)
            if diploma and diploma.user_id == current_user.id:
                maildiploma(os.path.join(basedir, app.config['SEND_FOLDER'], 'diploma_'+str(diploma.id)+".png"), current_user.mail)
                return render_template('/User.html', diplomas=tab_diploma, n=len(tab_diploma), diploma=diploma, success="Mail sent to "+current_user.mail+"!")
            else:
                return render_template('/User.html', diplomas=tab_diploma, n=len(tab_diploma), diploma=diploma, warning="Error!")
    else:
        return render_template('/User.html', diplomas=tab_diploma, n=len(tab_diploma), diploma=diploma)

@app.route("/admin",methods=['POST','GET'])
@login_required
def admin():
    if not check_admin(current_user.mail):
        return redirect('/')
    warning = None
    success = None
    if request.method == 'POST':
        if "otp" in request.form:
            otpverif = request.form["otpverif"]
            otp = request.form["otp"]
            diploma = Diploma.query.get(otp)
            if diploma and verifyotp(otpverif):
                diploma.status=1
                user = User.query.get(diploma.user_id)
                generate_unique_diploma(user,diploma)
                success = "Diploma validated !"
                maildiploma(os.path.join(basedir, app.config['SEND_FOLDER'],'diploma_'+str(diploma.id)+".png"),user.mail)
            else :
                warning = "Wrong OTP !"
        elif "refuse" in request.form:
            refuse = request.form["refuse"]
            diploma = Diploma.query.get(refuse)
            if diploma:
                diploma.status=0
                warning = "Diploma refused !"
    db.session.commit()
    tab_diploma = all_diplomas()
    return render_template('Admin.html', diplomas=tab_diploma, n=len(tab_diploma), admin=True, warning=warning, success=success)

@app.route("/otp",methods=['POST','GET'])
@login_required
def otp():
    if check_admin(current_user.mail):
        sendMail(current_user.mail)
        return "OTP Sent !"

if __name__ == '__main__' :
    with app.app_context():
        db.create_all()
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('FLASK_PORT', 8000))
    app.run(debug=debug, port=port)
