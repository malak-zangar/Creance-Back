from db import db
from datetime import datetime
from facture.view import *
from user.view import *

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
            'devise' : get_contrat_by_id(get_facture_by_id(self.facture_id)[0].json['facture']['contrat_id'])[0].json['contrat']['devise'],
            'actif' : self.actif,
            'facture' : get_facture_by_id(self.facture_id)[0].json['facture']['numero'],
            'client':  get_client_by_id(get_facture_by_id(self.facture_id)[0].json['facture']['client_id'])[0].json['client']['username'],
            'contrat' : get_contrat_by_id(get_facture_by_id(self.facture_id)[0].json['facture']['contrat_id'])[0].json['contrat']['reference']
        }


