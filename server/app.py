#!/usr/bin/env python3

# Standard library imports

# Remote library imports
from flask import request, session, jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, current_user

# Local imports
from config import app, db, api
from models import Customer, Item, Order, OrderItem

# JWT configuration
app.config["JWT_SECRET_KEY"] = "b'Y\xf1Xz\x01\xad|eQ\x80t \xca\x1a\x10K'"
app.config['JWT_TOKEN_LOCATION'] = ['headers']
jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Customer.query.filter_by(id=identity).one_or_none()

# Views go here!
class Signup(Resource):
    def post(self):
        data = request.get_json()

        try:
            new_customer = Customer(
                name=data['name'],
                username=data['username'],
                wallet=data['wallet'],
                admin=False
            )
            new_customer.password_hash = data['password']
            db.session.add(new_customer)
            db.session.commit()
            access_token = create_access_token(identity=new_customer)

            return make_response({"user": new_customer.to_dict(), 'access_token': access_token, 'admin': new_customer.admin}, 201)

        except Exception as e:
            print(f"Exception: {e}")  # Log the exception
            return make_response({'error': 'Invalid inputs'}, 400)

class CheckSession(Resource):
    @jwt_required()
    def get(self):
        return {**current_user.to_dict(), 'admin': current_user.admin}, 200

class Login(Resource):
    def post(self):
        data = request.get_json()

        check_customer = Customer.query.filter(Customer.username == data['username']).first()

        if check_customer and check_customer.authenticate(data['password']):
            access_token = create_access_token(identity=check_customer)
            return make_response({"user": check_customer.to_dict(), 'access_token': access_token, 'admin': check_customer.admin}, 200)

        return {'error': 'incorrect credentials'}, 401

class Logout(Resource):
    @jwt_required()
    def delete(self):
        # JWT doesn't have session management on server-side, so logout is handled on client side
        return {}, 204

class Home(Resource):
    def get(self):
        return '<h1> Phase 4 Project Server </h1>'

class Items(Resource):
    def get(self):
        items = [item.to_dict(rules=('-order_items',)) for item in Item.query.all()]
        return make_response(items, 200)

    def post(self):
        data = request.get_json()

        new_item = Item(
            title=data['title'],
            img_url=data['img_url'],
            description=data['description'],
            category=data['category'],
            price=data['price']
        )

        db.session.add(new_item)
        db.session.commit()

        return make_response(new_item.to_dict(), 201)

class ItemsByCategory(Resource):
    def get(self, category):
        category_items = [item.to_dict() for item in Item.query.filter(Item.category == category)]
        return (category_items, 200)

class ItemsByID(Resource):
    def get(self, id):
        item = Item.query.get(id)
        if item is None:
            return make_response({'error': 'Item not found'}, 404)
        return make_response(item.to_dict(rules=('-order_items',)), 200)

    def patch(self, id):
        item_to_update = Item.query.filter(Item.id == id).first()

        if item_to_update is None:
            return make_response({'error': 'Item not found'}, 404)

        for key in request.json:
            setattr(item_to_update, key, request.json[key])

        db.session.add(item_to_update)
        db.session.commit()

        return make_response(item_to_update.to_dict(), 202)

    def delete(self, id):
        item_to_delete = Item.query.filter(Item.id == id).first()
        if item_to_delete:
            db.session.delete(item_to_delete)
            db.session.commit()

            return make_response({'message': 'Item deleted'}, 200)
        else:
            return {'error': 'Item not found'}, 404

class Orders(Resource):
    def get(self):
        orders = [order.to_dict() for order in Order.query.all()]
        return make_response(orders, 200)

    def post(self):
        data = request.get_json()

        new_order = Order(
            customer_id=data['customer_id'],
            total=data['total']
        )
        db.session.add(new_order)
        db.session.commit()

        return make_response(new_order.to_dict(), 201)

class OrdersByID(Resource):
    def delete(self, id):
        order_to_delete = Order.query.filter(Order.id == id).first()
        if order_to_delete:
            db.session.delete(order_to_delete)
            db.session.commit()
            return make_response({'message': 'Order deleted'}, 200)
        else:
            return {'error': 'Order not found'}, 404

class OrderItems(Resource):
    def get(self):
        order_items = [order_item.to_dict() for order_item in OrderItem.query.all()]
        return make_response(order_items, 200)

    def post(self):
        data = request.get_json()

        new_order_item = OrderItem(
            quantity=data['quantity'],
            item_id=data['item_id'],
            order_id=data['order_id'],
        )

        db.session.add(new_order_item)
        db.session.commit()

        return make_response(new_order_item.to_dict(), 201)

class OrderItemByID(Resource):
    def get(self, id):
        order_item = OrderItem.query.filter(OrderItem.id == id).first()

        if order_item is None:
            return make_response({'error': 'OrderItem not found'}, 404)

        return make_response(order_item.to_dict(), 200)

    def patch(self, id):
        order_item = OrderItem.query.filter(OrderItem.id == id).first()

        if order_item is None:
            return make_response({'error': 'OrderItem not found'}, 404)

        for key in request.json:
            setattr(order_item, key, request.json[key])

        db.session.add(order_item)
        db.session.commit()

        return make_response(order_item.to_dict(), 200)

    def delete(self, id):
        order_item = OrderItem.query.filter(OrderItem.id == id).first()

        if order_item is None:
            return make_response({'error': 'OrderItem not found'}, 404)

        db.session.delete(order_item)
        db.session.commit()

        return make_response({'message': 'OrderItem deleted successfully'}, 200)

class Customers(Resource):
    def get(self):
        customers = Customer.query.all()
        customers_list = [customer.to_dict() for customer in customers]
        return make_response(customers_list, 200)

class CustomerByID(Resource):
    def get(self, id):
        customer = Customer.query.get(id)
        if customer:
            return make_response(customer.to_dict(), 200)
        return make_response({'message': 'Customer not found'}, 404)

    def patch(self, id):
        customer_to_update = Customer.query.get(id)
        if customer_to_update:
            data = request.get_json()

            if 'wallet' in data:
                setattr(customer_to_update, 'wallet', data['wallet'])
                db.session.add(customer_to_update)
                db.session.commit()
                return make_response(customer_to_update.to_dict(), 202)
            return make_response({'message': 'Invalid data'}, 400)

        return make_response({'message': 'Customer not found'}, 404)

    def delete(self, id):
        customer_to_delete = Customer.query.get(id)
        if customer_to_delete:
            db.session.delete(customer_to_delete)
            db.session.commit()
            return make_response({'message': 'Customer deleted'}, 200)
        return make_response({'message': 'Customer not found'}, 404)

api.add_resource(Home, '/')
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(Items, '/items')
api.add_resource(ItemsByCategory, '/items/<category>')
api.add_resource(ItemsByID, '/items/<int:id>')
api.add_resource(Orders, '/orders')
api.add_resource(OrdersByID, '/orders/<int:id>')
api.add_resource(OrderItems, '/orderitems')
api.add_resource(OrderItemByID, '/orderitems/<int:id>')
api.add_resource(Customers, '/customers')
api.add_resource(CustomerByID, '/customers/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
