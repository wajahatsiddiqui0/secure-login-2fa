from flask import Flask, render_template, request, redirect, url_for, session
import pyotp
import json
import qrcode
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()

        if username in users:
            return "Username already exists!"

        secret = pyotp.random_base32()
        users[username] = {'password': password, 'secret': secret}
        save_users(users)

        session['username'] = username

        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="SecureApp")
        qr = qrcode.make(uri)
        qr_path = f'static/{username}_qrcode.png'
        qr.save(qr_path)

        return render_template('register_done.html', username=username, qr_image=qr_path)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        user = users.get(username)

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('verify'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        token = request.form['token']
        username = session.get('username')

        if not username:
            return redirect(url_for('login'))

        users = load_users()
        secret = users[username]['secret']
        totp = pyotp.TOTP(secret)

        if totp.verify(token):
            return render_template('success.html', username=username)
        else:
            return "Invalid token. Please try again."
    return render_template('verify.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
