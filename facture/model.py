from db import db
from datetime import datetime


class Factures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero =  db.Column(db.String(80),nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    echeance = db.Column(db.DateTime,nullable=False )
    statut = db.Column(db.String(80),nullable=False)
    delai = db.Column(db.Integer )
    montant = db.Column(db.Float, nullable=False)
    montantEncaisse = db.Column(db.Float)
    dateFinalisation = db.Column(db.DateTime,nullable=False )
    solde = db.Column(db.Float)
    retard = db.Column(db.Integer)
    actionRecouvrement =  db.Column(db.String(80),nullable=False)
    actif = db.Column(db.Boolean,nullable=False)

    encaissements_facture = db.relationship('Encaissements', backref='facture', lazy=True)

    # Clé étrangère vers Users.id
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    


    def serialize(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'date': self.date,
            'echeance': self.echeance,
            'statut': self.statut,
            'delai':self.delai,
            'montant' : self.montant,
            'montantEncaisse' : self.montantEncaisse,
            'solde' : self.solde,
            'retard' : self.retard,
            'dateFinalisation' : self.dateFinalisation,
            'actionRecouvrement' : self.actionRecouvrement,
            'actif' : self.actif,
            'client_id' : self.client_id
        }

