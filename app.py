from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import random
import re
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於 session 儲存驗證碼

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        account = request.form.get('account', '').strip()
        password = request.form.get('password', '')
        users_path = os.path.join(os.path.dirname(__file__), 'users.json')
        with open(users_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        found = None
        # 判斷輸入的是電話還是帳號
        phone_pattern = r'^09\d{8}$'
        if re.match(phone_pattern, account):
            # 用電話比對
            for u in users_data['users']:
                if u['phone'] == account and u['password'] == password:
                    found = u
                    break
        else:
            # 用帳號比對
            for u in users_data['users']:
                if u['username'] == account and u['password'] == password:
                    found = u
                    break
        if found:
            session['user_phone'] = found['phone']
            session['user_name'] = found['username']
            return redirect(url_for('user_home'))
        else:
            error = '電話/帳號或密碼錯誤'
    return render_template('login.html', error=error)

# 消費者主頁：顯示所有餐廳
@app.route('/user_home')
def user_home():
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    stores = data.get('stores', [])
    return render_template('user_home.html', stores=stores)

# 餐廳菜單頁：顯示單一餐廳資料與菜單
@app.route('/store/<code>')
def store(code):
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data.get('stores', []):
        if s['code'] == code:
            store = s
            break
    if not store:
        return '找不到該餐廳', 404
    # 判斷是否在營業時間
    is_open = True
    try:
        from datetime import datetime, time as dtime
        open_t = store.get('open_time', '')
        close_t = store.get('close_time', '')
        if open_t and close_t:
            oh, om = map(int, open_t.split(':'))
            ch, cm = map(int, close_t.split(':'))
            ot = dtime(oh, om)
            ct = dtime(ch, cm)
            now = datetime.now().time()
            if ot <= ct:
                is_open = (ot <= now <= ct)
            else:
                # 跨午夜情況
                is_open = (now >= ot) or (now <= ct)
    except Exception:
        is_open = True
    return render_template('store.html', store=store, is_open=is_open)



@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    phone = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        phone_pattern = r'^09\d{8}$'
        if not re.match(phone_pattern, phone):
            error = '手機號碼格式錯誤'
        elif len(password) < 8:
            error = '密碼必須至少8位數'
        elif password != confirm_password:
            error = '密碼與確認密碼不一致'
        else:
            # 檢查電話不可重複
            users_path = os.path.join(os.path.dirname(__file__), 'users.json')
            with open(users_path, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            for u in users_data['users']:
                if u['phone'] == phone:
                    error = '此電話已註冊過帳號'
                    break
        if not error:
            try:
                print(f"[DEBUG] 準備寫入 users.json: {username}, {phone}, {password}")
                users_data['users'].append({
                    'username': username,
                    'phone': phone,
                    'password': password
                })
                with open(users_path, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, ensure_ascii=False, indent=2)
                print("[DEBUG] 寫入 users.json 成功！")
                return render_template('register_success.html')
            except Exception as e:
                print(f"[ERROR] 寫入 users.json 發生錯誤: {e}")
                error = f'系統錯誤：{e}'
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

        email_pattern = r'^\S+@\S+\.\S+$'
        phone_pattern = r'^09\d{8}$'  # 台灣手機格式


        # 檢查電話與 email 不可重複
        if not error:
            data_path = os.path.join(os.path.dirname(__file__), 'data.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for s in data['stores']:
                if s['owner_phone'] == owner_phone:
                    error = '此電話已註冊過店家帳號'
                    break
                if s['email'] == email:
                    error = '此 Email 已註冊過店家帳號'
                    break

        if not error:
            # 產生唯一店家代碼
            code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))
            data['stores'].append({
                'name': restaurant_name,
                'code': code,
                'password': code,  # 初始密碼為代碼，可自行修改
                'owner_phone': owner_phone,
                'email': email,
                'desc': '',
                'cover': '',
                'menu': []
            })
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 模擬寄信
            print(f"[寄信] 店家 {restaurant_name} 代碼：{code} 已寄到 {email}")
            return render_template('partner_success.html', code=code, email=email)

    return render_template('partner.html', error=error, restaurant_name=restaurant_name, owner_phone=owner_phone, email=email)


# 店家登入（名稱+密碼）
@app.route('/store_login', methods=['GET', 'POST'])
def store_login():
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('code', '').strip()
        data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        found = None
        for s in data['stores']:
            if s['name'] == name and s.get('password', s['code']) == password:
                found = s
                break
        if found:
            session['store_code'] = found['code']
            return redirect(url_for('store_admin'))
        else:
            error = '名稱或密碼錯誤'
    return render_template('store_login.html', error=error)


# 店家後台（需登入）
@app.route('/store_admin', methods=['GET'])
def store_admin():
    code = session.get('store_code')
    if not code:
        return redirect(url_for('store_login'))
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data['stores']:
        if s['code'] == code:
            store = s
            break
    if not store:
        return redirect(url_for('store_login'))
    return render_template('store_admin.html', store=store)

# 店家修改密碼頁
@app.route('/store_change_password', methods=['GET', 'POST'])
def store_change_password():
    code = session.get('store_code')
    if not code:
        return redirect(url_for('store_login'))
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data['stores']:
        if s['code'] == code:
            store = s
            break
    if not store:
        return redirect(url_for('store_login'))
    msg = error = None
    if request.method == 'POST':
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if old_password != store.get('password', store['code']):
            error = '舊密碼錯誤'
        elif len(new_password) < 4:
            error = '新密碼至少4碼'
        else:
            store['password'] = new_password
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            msg = '密碼已更新'
    return render_template('store_change_password.html', msg=msg, error=error)

from werkzeug.utils import secure_filename
@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    code = session.get('store_code')
    if not code:
        return redirect(url_for('store_login'))
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data['stores']:
        if s['code'] == code:
            store = s
            break
    if not store:
        return redirect(url_for('store_login'))

    # 處理圖片上傳
    img_url = ''
    img_file = request.files.get('item_img')
    if img_file and img_file.filename:
        filename = secure_filename(img_file.filename)
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        img_file.save(save_path)
        img_url = f'/static/uploads/{filename}'

    item = {
        'name': request.form.get('item_name', ''),
        'price': request.form.get('item_price', ''),
        'desc': request.form.get('item_desc', ''),
        'img': img_url
    }
    store['menu'].append(item)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return redirect(url_for('store_admin'))


# 店家發布剩餘數量（從前端 modal 提交）
@app.route('/publish_surplus', methods=['POST'])
def publish_surplus():
    code = session.get('store_code')
    if not code:
        return redirect(url_for('store_login'))
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data['stores']:
        if s['code'] == code:
            store = s
            break
    if not store:
        return redirect(url_for('store_login'))
    item_name = request.form.get('item_name', '')
    surplus = request.form.get('surplus', '0')
    try:
        surplus_val = int(surplus)
    except:
        surplus_val = 0
    for item in store.get('menu', []):
        if item.get('name') == item_name:
            item['surplus'] = surplus_val
            break
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return redirect(url_for('store_admin'))

# 店家主頁資料儲存
@app.route('/store_admin', methods=['POST'])
def store_admin_post():
    code = session.get('store_code')
    if not code:
        return redirect(url_for('store_login'))
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    store = None
    for s in data['stores']:
        if s['code'] == code:
            store = s
            break
    if not store:
        return redirect(url_for('store_login'))

    store['name'] = request.form.get('name', store['name'])
    store['address'] = request.form.get('address', store.get('address', ''))
    store['open_time'] = request.form.get('open_time', store.get('open_time', ''))
    store['close_time'] = request.form.get('close_time', store.get('close_time', ''))
    store['desc'] = request.form.get('desc', store.get('desc', ''))
    # 處理主頁圖片
    cover_file = request.files.get('cover')
    if cover_file and cover_file.filename:
        filename = secure_filename(cover_file.filename)
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        cover_file.save(save_path)
        store['cover'] = f'/static/uploads/{filename}'
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return redirect(url_for('store_admin'))

if __name__ == '__main__':
    app.run(debug=True)
