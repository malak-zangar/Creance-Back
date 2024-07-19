from db import db
from datetime import datetime

class ParamEntreprise(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    raisonSociale =  db.Column(db.String(80),nullable=False)
    adresse = db.Column(db.String(100),nullable=False)
    phone=db.Column(db.BigInteger,  nullable=False)
    email= db.Column(db.String(80),  nullable=False)
    identifiantFiscal = db.Column(db.String(80),  nullable=False)
    dateInsertion = db.Column(db.DateTime, nullable=False)

    contrats2 = db.relationship('Contrats', backref='param_entreprise', lazy=True)


    def serialize(self):
        return {
            'id': self.id,
            'raisonSociale': self.raisonSociale,
            'adresse': self.adresse,
            'phone': self.phone,
            'email':self.email,
            'identifiantFiscal' : self.identifiantFiscal,
            'dateInsertion': self.dateInsertion

        }


