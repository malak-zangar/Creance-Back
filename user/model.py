from db import db
from datetime import datetime


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email= db.Column(db.String(80), unique=True, nullable=False)
    phone=db.Column(db.BigInteger, unique=True, nullable=False)
    adresse = db.Column(db.String(80), nullable=False)
    
    actif = db.Column(db.Boolean,nullable=False)

    factures1 = db.relationship('Factures', backref='client', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'adresse': self.adresse,
            'actif' : self.actif
        }


