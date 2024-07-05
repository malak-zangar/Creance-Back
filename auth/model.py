from flask_login import UserMixin
from db import db
#from app import login_manager

class Auth(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def serialize(self):
        return {
                'id': self.id,
                'username': self.username,
                'password': self.password,
        }

    def is_active(self):
        return True




