import base64
from db import db
from client.view import *
from paramEntreprise.view import *

class Contrats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference =  db.Column(db.String(80),nullable=False)
    delai = db.Column(db.Integer, nullable=False)
    dateDebut = db.Column(db.DateTime, nullable=False)
    dateFin = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(80),nullable=False)
    total = db.Column(db.Float, nullable=True)
    prixJourHomme = db.Column(db.Float, nullable=True)
    typeFrequenceFacturation = db.Column(db.String(80),nullable=False)
    detailsFrequence = db.Column(db.String(100), nullable=True)
    montantParMois = db.Column(db.Float, nullable=True)
    devise = db.Column(db.String(80),nullable=False)
    contratFile = db.Column(db.LargeBinary, nullable=True)  
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
            'type':self.type,
            'total':self.total,
            'prixJourHomme':self.prixJourHomme,
            'typeFrequenceFacturation':self.typeFrequenceFacturation,
            'detailsFrequence' : self.detailsFrequence,
            'montantParMois':self.montantParMois,
            'devise': self.devise,
            'contratFile': base64.b64encode(self.contratFile).decode('utf-8') if self.contratFile else None,
            'client_id' : self.client_id,
            'client': self.client.username, 
            'paramentrep_id': self.paramentrep_id,
             
              }

    def serialize_for_export(self):
            return {
                'id': self.id,
                'reference': self.reference,
                'dateDebut': self.dateDebut,
                'dateFin': self.dateFin,
                'delai':self.delai,
                'type':self.type,
                'total':self.total,
                'prixJourHomme':self.prixJourHomme,
                'typeFrequenceFacturation':self.typeFrequenceFacturation,
                'detailsFrequence' : self.detailsFrequence,
                'montantParMois':self.montantParMois,
                'devise': self.devise,
                'paramentrep_id': self.paramentrep_id     
            }
