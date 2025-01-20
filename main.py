import os
from flask import Flask, render_template_string, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static'  # Папка для загрузки файлов
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Создание базы данных
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    events = Event.query.all()
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Интернет-афиша</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }
            .container { width: 80%; margin: 0 auto; padding-top: 20px; }
            .navbar { background-color: #cd65db; padding: 10px 0; text-align: center; }
            .navbar a { color: white; margin: 0 20px; text-decoration: none; font-size: 18px; }
            .event { background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            .event h3 { margin-top: 0; }
            .event img { max-width: 100%; height: auto; border-radius: 5px; margin-bottom: 20px;}
            .btn { background-color: #c727c4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px;}
            .btn:hover { background-color: #e092de; }
        </style>
    </head>
    <body>
        <div class="navbar">
            <a href="{{ url_for('home') }}">Главная</a>
            <a href="{{ url_for('logout') }}">Выход</a> 
            <a href="{{ url_for('add_event') }}">Добавить афишу</a>
        </div>
        <div class="container">
            <h1>Добро пожаловать на Мурмурция!</h1>
            {% if events %}
                {% for event in events %}
                    <div class="event">
                        <h3>Афиша: {{ event.name }}</h3>
                        <p><strong>Жанр:</strong> {{ event.genre }} <br>
                        <strong>Дата:</strong> {{ event.date }}</p>
                        <p>Описание: {{ event.description }}</p>
                        <img src="{{ url_for('static', filename = event.image) }}" alt="{{ event.name }}">
                        <br>
                        <a href="{{ url_for('edit_event', event_id=event.id) }}" class="btn">Редактировать</a>
                        <a href="{{ url_for('delete_event', event_id=event.id) }}" class="btn" style="background-color: #f44336;">Удалить</a>
                    </div>
                {% endfor %}
            {% else %}
                <p>Нет афиш для отображения.</p>
            {% endif %}
        </div>
    </body>
    </html>
    ''', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль!')
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Авторизация</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }
            .container { width: 300px; margin: 50px auto; padding: 20px; background-color: white; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            .btn { background-color: #c727c4; color: white; padding: 10px; width: 100%; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background-color: #e092de; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Авторизация</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit" class="btn">Войти</button>
            </form>
            <a href="{{ url_for('register') }}">Зарегистрироваться</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!')
        else:
            user = User(username=username, password=password_hash)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect(url_for('login'))
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Регистрация</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }
            .container { width: 300px; margin: 50px auto; padding: 20px; background-color: white; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            .btn { background-color: #c727c4; color: white; padding: 10px; width: 100%; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background-color: #e092de; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Регистрация</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit" class="btn">Зарегистрироваться</button>
            </form>
            <a href="{{ url_for('login') }}">Уже зарегистрированы? Войдите!</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        date = request.form['date']
        genre = request.form['genre']
        file = request.files['image']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename  # Здесь мы храним только имя файла
            
            user_id = session['user_id']
            event = Event(name=name, description=description, date=date, image=image_path, genre=genre, user_id=user_id)
            db.session.add(event)
            db.session.commit()
            
            flash('Афиша добавлена!')
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Добавить Афишу</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }
            .container { width: 80%; margin: 50px auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            input, textarea { width: 100%; padding: 10px; margin: 10px 0; }
            .btn { background-color: #c727c4; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; }
            .btn:hover { background-color: #e092de; }
            .otstup { margin-right: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Добавить Афишу</h2>
            <form method="POST" enctype="multipart/form-data" class = "otstup">
                <input type="text" name="name" placeholder="Название" required>
                <textarea name="description" placeholder="Описание" required></textarea>
                <input type="text" name="date" placeholder="Дата (например, 2025-01-20)" required>
                <input type="text" name="genre" placeholder="Жанр" required>
                <input type="file" name="image" required>
                <button type="submit" class="btn">Добавить</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    event = Event.query.get(event_id)
    
    if request.method == 'POST':
        event.name = request.form['name']
        event.description = request.form['description']
        event.date = request.form['date']

        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            event.image = f"/{filename}"


        event.genre = request.form['genre']
        db.session.commit()
        
        flash('Афиша обновлена!')
        return redirect(url_for('home'))
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Редактировать афишу</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }
            .container { width: 80%; margin: 50px auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            input, textarea { width: 100%; padding: 10px; margin: 10px 0; }
            .btn { background-color: #c727c4; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; }
            .btn:hover { background-color: #e092de; }
            .otstup { margin-right: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Редактировать Афишу</h2>
            <form method="POST" enctype="multipart/form-data", class = "otstup">
                <input type="text" name="name" value="{{ event.name }}" required>
                <textarea name="description" required>{{ event.description }}</textarea>
                <input type="text" name="date" value="{{ event.date }}" required>
                <input type="file" name="image" value="{{ event.image }}" required>
                <input type="text" name="genre" value="{{ event.genre }}" required>
                <button type="submit" class="btn">Обновить</button>
            </form>
        </div>
    </body>
    </html>
    ''', event=event)

@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    
    flash('Афиша удалена!')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
