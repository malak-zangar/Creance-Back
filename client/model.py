from contrat.view import get_contrat_by_client
from db import db
from datetime import datetime


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email= db.Column(db.String(80), unique=True, nullable=False)
    emailcc= db.Column(db.String(80),  nullable=False)
    phone=db.Column(db.BigInteger,  nullable=False)
    adresse = db.Column(db.String(80), nullable=False)
    identifiantFiscal = db.Column(db.String(80), unique=True, nullable=False)
    dateCreation = db.Column(db.DateTime, nullable=False)
    delaiRelance = db.Column(db.Integer,nullable=True)
    maxRelance = db.Column(db.Integer,nullable=True)

    actif = db.Column(db.Boolean,nullable=False)

    contrats1 = db.relationship('Contrats', backref='client', lazy=True)

    def serialize(self):
        current_date = datetime.now().date()  
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'emailcc': self.emailcc,
            'phone': self.phone,
            'adresse': self.adresse,
            'actif' : self.actif,
            'identifiantFiscal' : self.identifiantFiscal,
            'dateCreation': self.dateCreation,
            'delaiRelance':self.delaiRelance,
            'maxRelance':self.maxRelance,
            'contrats': [contrat.serialize() for contrat in self.contrats1],
            'contratsEncours': [
                contrat.serialize() for contrat in self.contrats1
                if contrat.dateDebut.date() <= current_date <= contrat.dateFin.date()
            ]
        }

    def serialize_for_export(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'emailcc': self.emailcc,
            'phone': self.phone,
            'adresse': self.adresse,
            'actif': self.actif,
            'identifiantFiscal': self.identifiantFiscal,
            'delaiRelance':self.delaiRelance,
            'maxRelance':self.maxRelance,
            'dateCreation': self.dateCreation,
            'contrats': [contrat.serialize_for_export() for contrat in self.contrats1]
        }

