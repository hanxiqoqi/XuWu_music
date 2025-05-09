from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from functools import wraps
import os
import json
import uuid
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Flask - Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 模拟用户数据库
users = {}
if os.path.exists('users.json'):
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"读取用户数据库时出错: {e}")

# 模拟音乐数据库
music_db = []
if os.path.exists('music_db.json'):
    try:
        with open('music_db.json', 'r') as f:
            music_db = json.load(f)
    except Exception as e:
        print(f"读取音乐数据库时出错: {e}")


# 用户类
class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


# 自动扫描目录函数
def scan_music_directory():
    music_dir = 'static/music'
    lrc_dir = 'static/lrc'
    for root, dirs, files in os.walk(music_dir):
        for file in files:
            if file.endswith(('.mp3', '.wav')):
                music_filename = file
                music_path = os.path.join(music_dir, music_filename)
                base_name = os.path.splitext(music_filename)[0]
                # 尝试从文件名中提取歌手信息
                parts = base_name.split(' - ')
                if len(parts) > 1:
                    title = ' - '.join(parts[:-1])
                    artist = parts[-1]
                else:
                    title = base_name
                    artist = "未知"
                lrc_filename = f'{base_name}.lrc'
                lrc_path = os.path.join(lrc_dir, lrc_filename)
                if os.path.exists(lrc_path):
                    lrc_exists = True
                else:
                    lrc_exists = False
                    lrc_filename = None
                    print(f"未找到 {base_name} 的歌词文件")

                new_music = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "artist": artist,
                    "category": "未知",
                    "music_file": music_filename,
                    "lrc_file": lrc_filename,
                    "comments": [],
                    "ratings": []
                }
                # 检查是否已经存在该音乐
                exists = False
                for music in music_db:
                    if music['music_file'] == music_filename:
                        exists = True
                        break
                if not exists:
                    music_db.append(new_music)

    try:
        with open('music_db.json', 'w') as f:
            json.dump(music_db, f)
    except Exception as e:
        print(f"保存音乐数据库时出错: {e}")


# 首页
@app.route('/')
@login_required
def index():
    scan_music_directory()
    all_music = music_db
    # 获取当前页码，默认为第 1 页
    page = request.args.get('page', 1, type=int)
    # 每页显示 12 首歌曲
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    limited_music_db = all_music[start:end]
    # 计算总页数
    total_pages = (len(all_music) + per_page - 1) // per_page
    # 首页查询词为空
    query = "" 

    return render_template('index.html', music_db=limited_music_db, page=page, total_pages=total_pages, query=query)


# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users:
            return "用户名已存在"

        # 移除管理员类型判断逻辑，直接创建普通用户
        users[username] = {"password": password, "playlists": [], "favorites": []}
        try:
            with open('users.json', 'w') as f:
                json.dump(users, f)
        except Exception as e:
            print(f"保存用户数据库时出错: {e}")
            return "注册失败，请稍后重试"
        return redirect(url_for('login'))

    return render_template('register.html')


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        stored_password = users.get(username, {}).get('password')
        if username in users and stored_password == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "用户名或密码错误"
    return render_template('login.html')


# 注销
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# 个人账号界面
@app.route('/account')
@login_required
def account():
    user_id = session.get('_user_id')
    user = users.get(user_id, {})
    return render_template('account.html', user=user, music_db=music_db)


# 音乐管理后台
@app.route('/music_management', methods=['GET', 'POST'])
@login_required
def music_management():
    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('artist')
        category = request.form.get('category')
        music_file = request.files.get('music_file')
        lrc_file = request.files.get('lrc_file')

        if music_file:
            music_filename = music_file.filename
            music_path = os.path.join('static/music', music_filename)
            music_file.save(music_path)

            lrc_filename = None
            if lrc_file:
                lrc_filename = lrc_file.filename
                lrc_path = os.path.join('static/lrc', lrc_filename)
                lrc_file.save(lrc_path)

            new_music = {
                "id": str(uuid.uuid4()),
                "title": title,
                "artist": artist,
                "category": category,
                "music_file": music_filename,
                "lrc_file": lrc_filename,
                "comments": [],
                "ratings": []
            }
            music_db.append(new_music)
            try:
                with open('music_db.json', 'w') as f:
                    json.dump(music_db, f)
            except Exception as e:
                print(f"保存音乐数据库时出错: {e}")
    return render_template('music_management.html', music_db=music_db)


# 删除音乐
@app.route('/delete_music/<music_id>', methods=['POST'])
@login_required
def delete_music(music_id):
    music_id = str(music_id)  # 将 music_id 转换为字符串
    for music in music_db:
        if str(music['id']) == music_id:  # 将 music['id'] 转换为字符串
            # 删除音乐文件
            music_file_path = os.path.join('static/music', music['music_file'])
            if os.path.exists(music_file_path):
                os.remove(music_file_path)
            # 删除歌词文件
            if music['lrc_file']:
                lrc_file_path = os.path.join('static/lrc', music['lrc_file'])
                if os.path.exists(lrc_file_path):
                    os.remove(lrc_file_path)
            # 从数据库中移除音乐记录
            music_db.remove(music)
            try:
                with open('music_db.json', 'w') as f:
                    json.dump(music_db, f)
            except Exception as e:
                print(f"保存音乐数据库时出错: {e}")
            break
    return redirect(url_for('music_management'))


# 音乐搜索
# 添加搜索路由，并添加登录验证
@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 12  # 每页显示 12 首歌曲
    scan_music_directory()
    results = []
    for music in music_db:
        if query in music['title'].lower() or query in music['artist'].lower():
            results.append(music)
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_results = results[start_index:end_index]
    
    total_pages = (len(results) + per_page - 1) // per_page
    
    return render_template('index.html', music_db=paginated_results, query=query, page=page, total_pages=total_pages)


# 创建播放列表
@app.route('/create_playlist', methods=['POST'])
@login_required
def create_playlist():
    user_id = session.get('_user_id')
    playlist_name = request.form.get('playlist_name')
    if user_id in users:
        users[user_id]['playlists'].append({"name": playlist_name, "musics": []})
        try:
            with open('users.json', 'w') as f:
                json.dump(users, f)
        except Exception as e:
            print(f"保存用户数据库时出错: {e}")
    return redirect(url_for('account'))


# 添加音乐到播放列表
@app.route('/add_to_playlist', methods=['POST'])
@login_required
def add_to_playlist():
    user_id = session.get('_user_id')
    playlist_name = request.form.get('playlist_name')
    music_id = str(request.form.get('music_id'))  # 将 music_id 转换为字符串
    if user_id in users:
        for playlist in users[user_id]['playlists']:
            if playlist['name'] == playlist_name:
                playlist['musics'].append(music_id)
                try:
                    with open('users.json', 'w') as f:
                        json.dump(users, f)
                except Exception as e:
                    print(f"保存用户数据库时出错: {e}")
    return jsonify({"status": "success"})


# 音乐推荐算法（简单示例）
def recommend_music(user_id):
    user = users.get(user_id)
    if user:
        favorites = user.get('favorites', [])
        favorite_categories = []
        for music_id in favorites:
            for music in music_db:
                if str(music['id']) == str(music_id):  # 将 music['id'] 和 music_id 转换为字符串
                    favorite_categories.append(music['category'])
        recommended = []
        for music in music_db:
            if music['category'] in favorite_categories and str(music['id']) not in favorites:  # 将 music['id'] 转换为字符串
                recommended.append(music)
        return recommended
    return music_db


# 音乐推荐页面
@app.route('/recommend')
@login_required
def recommend():
    user_id = session.get('_user_id')
    recommended_music = recommend_music(user_id)
    return render_template('index.html', music_db=recommended_music)


# 音乐评论和评分
@app.route('/comment_and_rate', methods=['POST'])
@login_required
def comment_and_rate():
    user_id = session.get('_user_id')
    music_id = str(request.form.get('music_id'))  # 将 music_id 转换为字符串
    comment = request.form.get('comment')
    rating = int(request.form.get('rating'))
    for music in music_db:
        if str(music['id']) == music_id:  # 将 music['id'] 转换为字符串
            music['comments'].append({"user": user_id, "comment": comment})
            music['ratings'].append(rating)
            try:
                with open('music_db.json', 'w') as f:
                    json.dump(music_db, f)
            except Exception as e:
                print(f"保存音乐数据库时出错: {e}")
    return jsonify({"status": "success"})


# 收藏音乐
@app.route('/favorite_music', methods=['POST'])
@login_required
def favorite_music():
    user_id = session.get('_user_id')
    music_id = str(request.form.get('music_id'))  # 将 music_id 转换为字符串
    if user_id in users:
        if music_id not in users[user_id]['favorites']:
            users[user_id]['favorites'].append(music_id)
            try:
                with open('users.json', 'w') as f:
                    json.dump(users, f)
            except Exception as e:
                print(f"保存用户数据库时出错: {e}")
    return jsonify({"status": "success"})


# 管理员权限装饰器
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        user_id = session.get('_user_id')
        if user_id in users and users[user_id]['is_admin']:
            return func(*args, **kwargs)
        else:
            abort(403)  # 禁止访问

    return decorated_view

# 删除管理员仪表盘相关代码
# @app.route('/admin_dashboard')
# @login_required
# @admin_required
# def admin_dashboard():
#     return render_template('admin_dashboard.html')

# 删除所有收藏记录
@app.route('/delete_all_favorites', methods=['POST'])
@login_required
def delete_all_favorites():
    user_id = session.get('_user_id')
    if user_id in users:
        users[user_id]['favorites'] = []
        try:
            with open('users.json', 'w') as f:
                json.dump(users, f)
        except Exception as e:
            print(f"保存用户数据库时出错: {e}")
    return jsonify({"status": "success", "message": "所有收藏记录已删除"})

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    user_id = session.get('_user_id')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        return "新密码和确认密码不一致"

    stored_password = users.get(user_id, {}).get('password')
    if stored_password != old_password:
        return "旧密码错误"

    users[user_id]['password'] = new_password
    try:
        with open('users.json', 'w') as f:
            json.dump(users, f)
    except Exception as e:
        print(f"保存用户数据库时出错: {e}")
        return "修改密码失败，请稍后重试"

    return "密码修改成功"

if __name__ == '__main__':
    if not os.path.exists('static/lrc'):
        os.makedirs('static/lrc')
    app.run(debug=True)
