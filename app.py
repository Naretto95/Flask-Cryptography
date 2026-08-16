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

def diploma_image_path(diploma_id):
    return os.path.join(basedir, app.config['SEND_FOLDER'], f"diploma_{diploma_id}.png")

def redirect_after_login(mail):
    return redirect('/admin') if check_admin(mail) else redirect('/diplomas')

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file_path = os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            code = decrypt_img(file_path)
            os.remove(file_path)
            return render_template('Index.html', success=f"QRCODE : {code[0]} STENO : {code[1]}")
        return render_template('Index.html', warning="File not found / Wrong type of file !")
    return render_template('Index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/login", methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method != 'POST':
        return render_template('Login.html')

    mail = request.form['email']
    password = request.form['password']
    authenticated, _ = authenticate(mail, password)
    if not authenticated:
        return render_template('Login.html', warning="Incorrect password/email combination !")
    return redirect_after_login(mail)

@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method != 'POST':
        return render_template('Register.html')

    email = request.form['email']
    if not is_email_available(email):
        return render_template('Register.html', warning="This email already exists!")

    user = {
        'email': email,
        'name': request.form['lname'],
        'first_name': request.form['fname'],
        'password': request.form['password'],
        'school': request.form['school'] if request.form['school'] in ["CYTECH", "EISTI"] else "CYTECH"
    }
    save_user(user)
    authenticate(user['email'], user['password'])
    return redirect_after_login(user['email'])

@app.route("/diplomas", methods=['POST', 'GET'])
@login_required
def diploma():
    if check_admin(current_user.mail):
        return redirect('/admin')
    tab_diploma = user_diploma(current_user.id)

    if request.method != 'POST':
        return render_template('User.html', diplomas=tab_diploma)

    if "certif" in request.form:
        new_diploma = {
            'user_id': current_user.id,
            'specialization': request.form['specialization'],
            'graduation_year': request.form['graduation_year'],
            'status': 2,
        }
        save_diploma(new_diploma)
        tab_diploma.append(new_diploma)
        return render_template('User.html', diplomas=tab_diploma, success="Diploma verification sent!")

    if "download" in request.form:
        target = Diploma.query.get(request.form["download"])
        if target and target.user_id == current_user.id:
            return send_file(diploma_image_path(target.id), as_attachment=True)
        return render_template('User.html', diplomas=tab_diploma, warning="Error!")

    if "mail" in request.form:
        target = Diploma.query.get(request.form["mail"])
        if target and target.user_id == current_user.id:
            maildiploma(diploma_image_path(target.id), current_user.mail)
            return render_template('User.html', diplomas=tab_diploma, success=f"Mail sent to {current_user.mail}!")
        return render_template('User.html', diplomas=tab_diploma, warning="Error!")

    return render_template('User.html', diplomas=tab_diploma)

@app.route("/admin",methods=['POST','GET'])
@login_required
def admin():
    if not check_admin(current_user.mail):
        return redirect('/')

    warning = None
    success = None
    if request.method == 'POST':
        if "otp" in request.form:
            target = Diploma.query.get(request.form["otp"])
            if target and verifyotp(request.form["otpverif"]):
                target.status = 1
                user = User.query.get(target.user_id)
                generate_unique_diploma(user, target)
                maildiploma(diploma_image_path(target.id), user.mail)
                success = "Diploma validated !"
            else:
                warning = "Wrong OTP !"
        elif "refuse" in request.form:
            target = Diploma.query.get(request.form["refuse"])
            if target:
                target.status = 0
                warning = "Diploma refused !"
        db.session.commit()

    tab_diploma = all_diplomas()
    return render_template('Admin.html', diplomas=tab_diploma, warning=warning, success=success)

@app.route("/otp",methods=['POST','GET'])
@login_required
def otp():
    if not check_admin(current_user.mail):
        return "Forbidden", 403
    sendMail(current_user.mail)
    return "OTP Sent !"

if __name__ == '__main__' :
    with app.app_context():
        db.create_all()
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('FLASK_PORT', 8000))
    app.run(debug=debug, port=port)
