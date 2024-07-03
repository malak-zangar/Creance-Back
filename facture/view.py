from flask import Blueprint, request, jsonify, make_response, redirect, flash, render_template
from datetime import datetime, timedelta
from facture.model import Factures
from db import db

facture = Blueprint('facture', __name__, url_prefix='/facture')


#Add new facture
@facture.route('/create', methods=['POST'])
def create_facture():
    data = request.get_json()
    numero = data.get("numero")
    date = data.get("date")
    echeance = data.get("echeance")
    statut = data.get("statut")
    delai = data.get("delai")
    montant = data.get("montant")
    montantEncaisse = data.get("montantEncaisse")
    solde = data.get("solde")
    retard = data.get("retard")
    dateFinalisation = data.get("dateFinalisation")
    actionRecouvrement = data.get("actionRecouvrement")
    client_id = data.get("client_id")
    actif = True

    if not (numero and date and echeance and statut and delai and montant 
            and montantEncaisse and solde and retard and dateFinalisation
             and actionRecouvrement and client_id ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    
  
    if Factures.query.filter_by(numero=numero).first() is not None:
        return jsonify({'erreur': "Numéro de facture existe déja"}), 409


    new_facture = Factures(numero=numero, date=date,echeance=echeance,statut=statut,delai=delai,montant=montant,
                montantEncaisse=montantEncaisse, solde=solde, retard=retard, dateFinalisation=dateFinalisation,
                   actionRecouvrement=actionRecouvrement, actif=actif ,client_id=client_id )
    db.session.add(new_facture)
    db.session.commit()
    return make_response(jsonify({"message": "facture crée avec succes", "facture": new_facture.serialize()}), 201)


#GetAll factures
@facture.route('/getAll', methods=['GET'])
def get_all_factures():
    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]
    return jsonify(serialized_factures)

#GetActiffactures
@facture.route('/getAllActif', methods=['GET'])
def get_all_actif_factures():
    actif_factures = Factures.query.filter_by(actif=True).all()
    serialized_factures = [facture.serialize() for facture in actif_factures]
    return jsonify(serialized_factures)

#GetArchivedfactures
@facture.route('/getAllArchived', methods=['GET'])
def get_all_archived_factures():
    archived_factures = Factures.query.filter_by(actif=False).all()
    serialized_factures = [facture.serialize() for facture in archived_factures]
    return jsonify(serialized_factures)


#GetfactureByID
@facture.route('/getByID/<int:id>',methods=['GET'])
def get_facture_by_id(id):
    facture = Factures.query.get(id)

    if not facture:
        
        return jsonify({"message": "facture n'existe pas"}), 404

    
    return jsonify({
        'message': "facture existe :",
        'facture': facture.serialize()
    }), 200

#Archivefacture
@facture.route('/archiveFacture/<int:id>',methods=['PUT'])
def archiverFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404
    
    facture.actif=False

    try:
        db.session.commit()
        return jsonify({"message": "facture archivé avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans l'archivage du facture"}), 500
    

#Updatefacture
@facture.route('/updateFacture/<int:id>',methods=['PUT'])
def updateFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404

    data = request.get_json()
    facture.numero = data.get("numero",facture.numero)
    facture.date = data.get("date",facture.date)
    facture.echeance = data.get("echeance",facture.echeance)
    facture.statut = data.get("statut",facture.statut)
    facture.delai = data.get("delai",facture.delai)
    facture.montant = data.get("montant",facture.montant)
    facture.montantEncaisse = data.get("montantEncaisse",facture.montantEncaisse)
    facture.solde = data.get("solde",facture.solde)
    facture.retard = data.get("retard",facture.retard)
    facture.dateFinalisation = data.get("dateFinalisation",facture.dateFinalisation)
    facture.actionRecouvrement = data.get("actionRecouvrement",facture.actionRecouvrement)
    facture.client_id = data.get("client_id",facture.client_id)
    facture.actif = data.get("actif",facture.actif)

    try:
        db.session.commit()
        return jsonify({"message": "facture modifiée avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de la facture"}), 500