from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import random
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於 session 儲存驗證碼

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 這裡可以加入驗證邏輯
        return redirect(url_for('index'))
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    phone = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        phone = request.form.get('phone', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        phone_pattern = r'^09\d{8}$'
        if not re.match(phone_pattern, phone):
            error = '手機號碼格式錯誤'
        elif len(password) < 8:
            error = '密碼必須至少8位數'
        elif password != confirm_password:
            error = '密碼與確認密碼不一致'
        # 這裡可加帳號重複檢查等

        if not error:
            return redirect(url_for('login'))
    return render_template('register.html', error=error, phone=phone)





# 餐廳合作夥伴申請
@app.route('/partner', methods=['GET', 'POST'])
def partner():
    error = None
    restaurant_name = ''
    owner_phone = ''
    email = ''
    if request.method == 'POST':
        restaurant_name = request.form.get('restaurant_name', '')
        owner_phone = request.form.get('owner_phone', '')
        email = request.form.get('email', '')

        import re
        email_pattern = r'^\S+@\S+\.\S+$'
        phone_pattern = r'^09\d{8}$'  # 台灣手機格式

        if not re.match(email_pattern, email):
            error = 'Email 格式錯誤'
        elif not re.match(phone_pattern, owner_phone):
            error = '電話格式錯誤，請輸入 09 開頭的 10 碼手機號碼'

        if not error:
            # 這裡可以加入資料儲存或通知邏輯
            return '<h2>感謝您的申請，我們會盡快與您聯繫！</h2>'

    return render_template('partner.html', error=error, restaurant_name=restaurant_name, owner_phone=owner_phone, email=email)

if __name__ == '__main__':
    app.run(debug=True)
