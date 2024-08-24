from db import db
from datetime import datetime
from paramEntreprise.view import get_paramentrep_by_id, get_paramentrep_by_id1
from client.view import *

class Factures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero =  db.Column(db.String(80),nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    echeance = db.Column(db.DateTime,nullable=False )
    statut = db.Column(db.String(80),nullable=False)
    #delai = db.Column(db.Integer )
    montant = db.Column(db.Float, nullable=False)
    montantEncaisse = db.Column(db.Float)
    dateFinalisation = db.Column(db.DateTime)
    solde = db.Column(db.Float)
    retard = db.Column(db.Integer)
    actif = db.Column(db.Boolean,nullable=False)
    nbrRelance = db.Column(db.Integer, nullable=False)
    # actifRelance = db.Column(db.Boolean,nullable=False)

    encaissements_facture = db.relationship('Encaissements', backref='facture', lazy=True)

    contrat_id = db.Column(db.Integer, db.ForeignKey('contrats.id'), nullable=False)


    def serialize(self):
        from contrat.view import get_contrat_by_id
        from client.view import get_client_by_id
        # from dashboard.utils import get_contrat_by_id


        return {
            'id': self.id,
            'numero': self.numero,
            'date': self.date,
            'echeance': self.echeance,
            'statut': self.statut,
            'delai':get_contrat_by_id(self.contrat_id)[0].json['contrat']['delai'],
            'montant' : self.montant,
            'montantEncaisse' : self.montantEncaisse,
            'solde' : self.solde,
            'retard' : self.retard,
            'dateFinalisation' : self.dateFinalisation,
            'actif' : self.actif,
            'contrat_id' : self.contrat_id,
            'nbrRelance' : self.nbrRelance,
            'contrat' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['reference'],
            'devise' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['devise'],
            'client_id' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'],
            'client': get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['username'],
            'maxRelance' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['maxRelance'],
            'delaiRelance' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['delaiRelance'],
            'email' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email'],

 }
    def serializeForEmail(self):
        from contrat.utils import get_contrat_by_id
        # from client.view import get_client_by_id
        # from dashboard.utils import get_contrat_by_id
        from client.utils import get_client_by_id


        return {
            'id': self.id,
            'numero': self.numero,
            'date': self.date,
            'echeance': self.echeance,
            'statut': self.statut,
            'delai': get_contrat_by_id(self.contrat_id)[0].json['contrat']['delai'],
            'montant' : self.montant,
            'montantEncaisse' : self.montantEncaisse,
            'solde' : self.solde,
            'retard' : self.retard,
            'dateFinalisation' : self.dateFinalisation,
            'actif' : self.actif,
            'contrat_id' : self.contrat_id,
            'nomEntrep' : get_paramentrep_by_id1(get_contrat_by_id(self.contrat_id)[0].json['contrat']['paramentrep_id'])[0].json['paramentreprise']['raisonSociale'],
            'nbrRelance' : self.nbrRelance,
            'contrat' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['reference'],
            'devise' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['devise'],
            'client_id' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'],
            'client': get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['username'],
            'maxRelance' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['maxRelance'],
            'delaiRelance' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['delaiRelance'],
            'email' : get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email'],

 }

    def serialize_for_export(self):
        from contrat.view import get_contrat_by_id
        from client.view import get_client_by_id

        return {
            'id': self.id,
            'numero': self.numero,
            'date': self.date,
            'echeance': self.echeance,
            'statut': self.statut,
            'delai':get_contrat_by_id(self.contrat_id)[0].json['contrat']['delai'],
            'montant' : self.montant,
            'montantEncaisse' : self.montantEncaisse,
            'solde' : self.solde,
            'retard' : self.retard,
            'dateFinalisation' : self.dateFinalisation,
            'actif' : self.actif,
            'nbrRelance' : self.nbrRelance,
            'contrat' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['reference'],
            'devise' : get_contrat_by_id(self.contrat_id)[0].json['contrat']['devise'],
            'client': get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['username'],
        }
    
    def serialize_for_bill(self):
        from contrat.view import get_contrat_by_id
        from client.view import get_client_by_id

        return {
            'id': self.id,
            'numero': self.numero,
            'date': self.date,
            'echeance': self.echeance,
            'statut': self.statut,
            'montant' : self.montant,
            'montantEncaisse' : self.montantEncaisse,
            'solde' : self.solde,
            'retard' : self.retard,
            'dateFinalisation' : self.dateFinalisation,
            'nbrRelance' : self.nbrRelance,
            'contrat' : get_contrat_by_id(self.contrat_id)[0].json['contrat'],
            'param_entreprise' : get_paramentrep_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['paramentrep_id'])[0].json['paramentreprise'],
            'client': get_client_by_id(get_contrat_by_id(self.contrat_id)[0].json['contrat']['client_id'])[0].json['client'],
        }

