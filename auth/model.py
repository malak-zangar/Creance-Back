import time
import os
from flask import current_app
from flask_login import UserMixin
import jwt
from db import db

class Auth(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email= db.Column(db.String(150),unique=True,  nullable=False)

    def get_reset_token(self, expires_sec=1800): 
  
        return jwt.encode({'reset_password': self.username,
                           'exp': time.time() + expires_sec},
                           key=os.getenv('SECRET_KEY'))

    def verify_reset_token(token):
        try:
            username = jwt.decode(token,
              key=os.getenv('SECRET_KEY'))['reset_password']
        except Exception as e:
            print(e)
            return
        return Auth.query.filter_by(username=username).first()
    
    def serialize(self):
        return {
                'id': self.id,
                'username': self.username,
                'password': self.password,
                'email': self.email,
        }

    def is_active(self):
        return True




