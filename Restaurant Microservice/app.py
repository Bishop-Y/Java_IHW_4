# Импортируем необходимые библиотеки и модули
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt_header, get_jwt
import requests
import os

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


# Определяем модель Dish для SQLAlchemy
class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())


# Определяем модель Order для SQLAlchemy
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False, server_default="pending")
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())


# Определяем модель OrderDish для SQLAlchemy
class OrderDish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# Этот метод обрабатывает POST-запрос для создания нового заказа
@app.route('/order', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()  # Получение уникального идентификатора пользователя из JWT
    data = request.get_json()  # Получение данных из JSON запроса
    dish_list = data.get('dishes')  # Получение списка блюд из данных
    special_requests = data.get('special_requests')  # Получение специальных требований из данных
    # Проверка валидности списка блюд
    if not dish_list or not isinstance(dish_list, list):
        return {"message": "Invalid data"}, 400

    # Создание нового заказа с user_id и специальными требованиями
    order = Order(user_id=user_id, special_requests=special_requests)
    db.session.add(order)
    db.session.commit()
    # Проходим по всем блюдам в списке и добавляем их в заказ
    for dish in dish_list:
        dish_id = dish.get('id')
        quantity = dish.get('quantity')
        dish_obj = Dish.query.get(dish_id)
        # Проверка доступности блюда и достаточного количества
        if not dish_obj or dish_obj.quantity < quantity:
            return {"message": "Dish not available or quantity exceeded"}, 400
        else:
            # Уменьшаем количество блюда на складе
            dish_obj.quantity -= quantity
            # Создаем запись о заказе и блюде в таблице OrderDish
            order_dish = OrderDish(order_id=order.id, dish_id=dish_id, quantity=quantity, price=dish_obj.price)
            db.session.add(order_dish)
    db.session.commit()
    # Возвращаем сообщение об успешном создании заказа и его ID
    return {
        "message": "Order Created",
        "order_id": order.id
    }, 201


# Этот метод обрабатывает GET-запрос для получения информации о конкретном заказе по его ID
@app.route('/order/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_by_id(order_id):
    order = Order.query.get(order_id)  # Получаем заказ по его ID
    # Если заказ не найден, возвращаем сообщение об ошибке
    if not order:
        return {"message": "Order not found"}, 404
    # Если заказ найден, возвращаем его ID и статус
    else:
        return {
            "order_id": order.id,
            "status": order.status
        }, 200



# Этот метод вызывается для получения информации о пользователе по его токену
def get_user_info(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get("http://localhost:6700/auth/user", headers=headers)
    # Если получить информацию о пользователе не удалось, возвращаем сообщение об ошибке
    if response.status_code != 200:
        return {'message': 'Failed to get user info'}, 404
    # Если информация получена успешно, возвращаем ее
    else:
        return response.json()

# Этот метод обрабатывает различные HTTP-запросы для управления блюдами (создание, просмотр, обновление и удаление)
@app.route('/dish', methods=['POST', 'GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_dish():
    token = request.headers.get('Authorization')
    token = token[7:]
    data = get_user_info(token)
    # Если роль пользователя не 'manager', возвращаем полученные данные
    if data.get('role') != 'manager':
        return data
    print(request.method)
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        quantity = data.get('quantity')

        new_dish = Dish(name=name, description=description, price=price, quantity=quantity)
        db.session.add(new_dish)
        db.session.commit()

        return {
            "message": "Dish Created",
            "dish_id": new_dish.id
        }, 201

    elif request.method == 'GET':
        dishes = Dish.query.all()
        all_dishes = []
        for dish in dishes:
            all_dishes.append(
                {"name": dish.name,
                 "description": dish.description,
                  "price": dish.price,
                  "quantity": dish.quantity}
            )
        return {"dishes": all_dishes}, 200

    elif request.method == 'PUT':
        data = request.get_json()
        dish_id = data.get('id')
        dish_obj = Dish.query.get(dish_id)
        if not dish_obj:
            return {"message": "Dish not found"}, 404
        dish_obj.name = data.get('name', dish_obj.name)
        dish_obj.description = data.get('description', dish_obj.description)
        dish_obj.price = data.get('price', dish_obj.price)
        dish_obj.quantity = data.get('quantity', dish_obj.quantity)
        db.session.commit()
        return {
            "message": "Dish Updated",
            "dish_id": dish_id
        }, 200

    elif request.method == 'DELETE':
        dish_id = request.get_json().get('id')
        dish_obj = Dish.query.get(dish_id)
        if not dish_obj:
            return {"message": "Dish not found"}, 404
        db.session.delete(dish_obj)
        db.session.commit()

        return {
            "message": "Dish Deleted",
            "dish_id": dish_id
        }, 200


# Этот метод обрабатывает GET-запрос для получения списка доступных блюд
@app.route('/menu', methods=['GET'])
def get_menu():
    # Получаем все доступные блюда из базы данных
    available_dishes = Dish.query.filter(Dish.is_available == True).all()

    menu = []
    # Создаем список из информации о доступных блюдах
    for dish in available_dishes:
        menu.append({
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "quantity": dish.quantity
        })

    # Если нет доступных блюд, возвращаем сообщение об ошибке
    if len(menu) == 0:
        return {"message": "No dishes available at the moment"}, 404

    # Возвращаем список доступных блюд
    return {"menu": menu}, 200



# Точка входа в приложение
if __name__ == "__main__":
    # Создаем все таблицы базы данных, определенные в моделях
    with app.app_context():
        db.create_all()
    # Запускаем приложение на порту 6900
    app.run(port=6900)
