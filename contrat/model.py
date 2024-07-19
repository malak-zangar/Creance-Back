from db import db
from datetime import datetime
from user.view import *
from paramEntreprise.view import *

class Contrats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference =  db.Column(db.String(80),nullable=False)
    delai = db.Column(db.Integer, nullable=False)
    dateDebut = db.Column(db.DateTime, nullable=False)
    dateFin = db.Column(db.DateTime, nullable=False)
    conditionsFinancieres = db.Column(db.String(200),nullable=False)
    prochaineAction = db.Column(db.String(200),nullable=False)
    dateProchaineAction = db.Column(db.DateTime,nullable=False)
    dateRappel = db.Column(db.DateTime,nullable=False)
    
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    factures1 = db.relationship('Factures', backref='contrat', lazy=True)
    paramentrep_id = db.Column(db.Integer, db.ForeignKey('param_entreprise.id'), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'reference': self.reference,
            'dateDebut': self.dateDebut,
            'dateFin': self.dateFin,
            'delai':self.delai,
            'conditionsFinancieres' : self.conditionsFinancieres,
            'prochaineAction' : self.prochaineAction,
            'dateProchaineAction' : self.dateProchaineAction,
            'dateRappel' : self.dateRappel,
            'client_id' : self.client_id,
            'client': get_client_by_id(self.client_id)[0].json['client']['username'],
            'paramentrep_id': self.paramentrep_id        }


