from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property

from config import db, bcrypt

# Models go here!

class Customer(db.Model, SerializerMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    wallet = db.Column(db.Float)
    admin = db.Column(db.Boolean)

    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    orders = db.relationship('Order', backref='customer')
    order_items = association_proxy('orders', 'order_items')

    serialize_rules = ('-_password_hash', '-orders', '-created_at', '-updated_at')

    @validates('name')
    def validate_name(self, key, name):
        if not name:
            raise ValueError('Customer must have a name')
        return name

    @hybrid_property
    def password_hash(self):
        return self._password_hash
    
    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')
    
    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))

class Item(db.Model, SerializerMixin):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    img_url = db.Column(db.String)
    description = db.Column(db.String)
    category = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer)

    order_items = db.relationship('OrderItem', backref='item')

    serialize_rules = ('-order_items', '-created_at', '-updated_at')

    @validates('category')
    def validate_category(self, key, category):
        if not category:
            raise ValueError('Category cannot be empty. Must be firearm, accessory or ammunition.')
        return category

    @validates('price')
    def validate_price(self, key, price):
        if not price and 1 <= price:
            raise ValueError('Must have a price of 1 or more')
        return price

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    total = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    order_items = db.relationship('OrderItem', backref='order')
    items = association_proxy('order_items', 'item')

    serialize_rules = ('-order_items', '-customer_id', 'updated_at')


class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'orderitems'

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    serialize_rules = ('-created_at', '-updated_at', 'order', '-order_id', '-item_id')

    @validates('quantity')
    def validate_quantity(self, key, quantity):

        if quantity > 0:
            return quantity
        else:
            raise ValueError('Quantity must be greater than 0')