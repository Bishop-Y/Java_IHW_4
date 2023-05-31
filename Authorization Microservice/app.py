# Импортируем необходимые библиотеки и модули
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint
from datetime import timedelta
import os
import datetime

# Создаём новый объект Flask, который представляет наше веб-приложение
app = Flask(__name__)

# Устанавливаем конфигурацию для Flask-приложения.
# Задаём URL базы данных для SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://amepifanov:fhntv2003@localhost:5050/postgres'
# Генерируем ключ для шифрования JWT
app.config['JWT_SECRET_KEY'] = 'hfsdaifhodifh2176419_901ns70-252'

# Создаём объекты SQLAlchemy и JWTManager
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Определяем модель User для SQLAlchemy
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Задаём ограничение на возможные значения ролей пользователей
    __table_args__ = (
        CheckConstraint(role.in_(['customer', 'chef', 'manager'])),
    )


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Ссылка на связанного пользователя
    user = db.relationship('User', backref='sessions', lazy=True)



# Создаём endpoint '/register' для регистрации пользователя
@app.route('/register', methods=['POST'])
def register():
    # Получаем данные из запроса
    data = request.get_json()

    # Проверка наличия всех необходимых полей
    if not all(field in data for field in ("username", "email", "password")):
        return {"message": "Missing required fields!"}, 400

    # Проверка корректности роли
    if "role" in data and data["role"] not in ("customer", "chef", "manager"):
        return {"message": "Invalid role provided!"}, 400

    # Проверка корректности email
    if '@' not in data['email']:
        return {"message": "Email has not '@' symbol"}, 400

    # Проверка наличия пользователя с таким email
    if User.query.filter_by(email=data['email']).first():
        return {"message": "User with given email already exists!"}, 400

    hashed_password = generate_password_hash(data['password'], method='scrypt')

    # Создание пользователя с указанной ролью или ролью по умолчанию
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password, role=data.get("role", "customer"))

    db.session.add(new_user)
    db.session.commit()

    return {"message": "New user created!"}, 201


# Создаём endpoint '/login' для аутентификации пользователей
@app.route('/login', methods=['POST'])
def login():
    # Получаем данные из запроса
    data = request.get_json()
    # Проверяем наличие пользователя с указанным email
    user = User.query.filter_by(email=data['email']).first()

    # Если пользователь не найден, или пароль не верный, возвращаем ошибку
    if not user or not check_password_hash(user.password_hash, data['password']):
        return {"message": "Invalid credentials!"}, 401

    # Создаем JWT для аутентифицированного пользователя
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=30))
    # Создаем новую сессию в таблице сессий с данными пользователя и токеном
    new_session = Session(user_id=user.id, session_token=access_token, expires_at=datetime.datetime.now() + timedelta(minutes=30))
    db.session.add(new_session)
    db.session.commit()

    # Возвращаем JWT в ответе
    return {"access_token": access_token}, 200


@app.route('/user', methods=['GET'])
@jwt_required()
def user_info():
    # Идентификатор пользователя сохраняется в JWT
    user_id = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return {"message": "User not found!"}, 404

    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }, 200

# Точка входа в приложение
if __name__ == "__main__":
    # Создаем все таблицы базы данных, определенные в моделях
    with app.app_context():
        db.create_all()
    # Запускаем приложение на порту 6800
    app.run(port=6800)