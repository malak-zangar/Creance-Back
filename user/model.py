from db import db
from datetime import datetime


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # You can customize the rest as you want add email, status, name, etc...

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username
        }


