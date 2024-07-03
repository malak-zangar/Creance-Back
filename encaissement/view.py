from flask import Blueprint, request, jsonify, make_response, redirect, flash, render_template
from datetime import datetime, timedelta
from encaissement.model import Encaissements
from db import db

encaissement = Blueprint('encaissement', __name__, url_prefix='/encaissement')


#Add new encaissement
@encaissement.route('/create', methods=['POST'])
def create_encaissement():
    data = request.get_json()
    date = data.get("date")
    modeReglement = data.get("modeReglement")
    montantEncaisse = data.get("montantEncaisse")
    reference = data.get("reference")
    facture_id = data.get("facture_id")
    actif = True

    if not (modeReglement and date and reference and facture_id and montantEncaisse ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    
  
    if Encaissements.query.filter_by(reference=reference).first() is not None:
        return jsonify({'erreur': "Référence d'encaissement existe déja"}), 409


    new_encaissement = Encaissements(modeReglement=modeReglement, date=date,montantEncaisse=montantEncaisse,reference=reference,
       facture_id=facture_id,actif=actif)
    db.session.add(new_encaissement)
    db.session.commit()
    return make_response(jsonify({"message": "encaissement crée avec succes", "encaissement": new_encaissement.serialize()}), 201)


#GetAll encaissement
@encaissement.route('/getAll', methods=['GET'])
def get_all_encaissements():
    encaissements = Encaissements.query.all()
    serialized_encaissements = [encaissement.serialize() for encaissement in encaissements]
    return jsonify(serialized_encaissements)

#GetActifencaissements
@encaissement.route('/getAllActif', methods=['GET'])
def get_all_actif_encaissements():
    actif_encaissements = Encaissements.query.filter_by(actif=True).all()
    serialized_encaissements = [facture.serialize() for facture in actif_encaissements]
    return jsonify(serialized_encaissements)

#GetArchivedencaissements
@encaissement.route('/getAllArchived', methods=['GET'])
def get_all_archived_encaissements():
    archived_encaissements = Encaissements.query.filter_by(actif=False).all()
    serialized_encaissements = [encaissement.serialize() for encaissement in archived_encaissements]
    return jsonify(serialized_encaissements)


#GetfactureByID
@encaissement.route('/getByID/<int:id>',methods=['GET'])
def get_encaissement_by_id(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        
        return jsonify({"message": "encaissement n'existe pas"}), 404

    
    return jsonify({
        'message': "encaissement existe :",
        'encaissement': encaissement.serialize()
    }), 200

#Archivefacture
@encaissement.route('/archiveEncaissement/<int:id>',methods=['PUT'])
def archiverEncaissement(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        return jsonify({"message": "encaissement n'existe pas"}), 404
    
    encaissement.actif=False

    try:
        db.session.commit()
        return jsonify({"message": "encaissement archivé avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans l'archivage de l'encaissement"}), 500
    

#Updatefacture
@encaissement.route('/updateEncaissement/<int:id>',methods=['PUT'])
def updateEncaissement(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        return jsonify({"message": "encaissement n'existe pas"}), 404

    data = request.get_json()
    encaissement.date = data.get("date",encaissement.date)
    encaissement.reference = data.get("reference",encaissement.reference)
    encaissement.montantEncaisse = data.get("montantEncaisse",encaissement.montantEncaisse)
    encaissement.modeReglement = data.get("modeReglement",encaissement.modeReglement)
    encaissement.facture_id = data.get("facture_id",encaissement.facture_id)
    encaissement.actif = data.get("actif",encaissement.actif)

    try:
        db.session.commit()
        return jsonify({"message": "encaissement modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de l'encaissement"}), 500