from db import db
from datetime import datetime


class Encaissements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime,nullable=False)
    modeReglement = db.Column(db.String(80),nullable=False)
    montantEncaisse = db.Column(db.Float,nullable=False)
    reference = db.Column(db.String(80),nullable=False)

    actif = db.Column(db.Boolean,nullable=False)

#relation

    facture_id = db.Column(db.Integer, db.ForeignKey('factures.id'),nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'date': self.date,
            'modeReglement' : self.modeReglement,
            'montantEncaisse' : self.montantEncaisse,
            'reference' : self.reference,
            'facture_id' : self.facture_id,
            'actif' : self.actif,
        }


