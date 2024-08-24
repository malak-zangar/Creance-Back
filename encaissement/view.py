import json
from flask import Blueprint, request, jsonify, make_response, redirect, flash, render_template
from datetime import datetime, timedelta
from encaissement.model import Encaissements
from facture.model import Factures
from facture.utils import updateFactureAfterCancelEncaissement, updateFactureAfterEncaissement
from facture.view import *
from db import db
from flask_jwt_extended import jwt_required

encaissement = Blueprint('encaissement', __name__, url_prefix='/encaissement')


#Add new encaissement
@encaissement.route('/create', methods=['POST'])
@jwt_required()
def create_encaissement():
    data = request.get_json()
    date = data.get("date")        
    modeReglement = data.get("modeReglement")
    montantEncaisse = float(data.get("montantEncaisse"))
    reference = data.get("reference")
    facture_numero = data.get("facture_numero")
   # actif = True

    if not (modeReglement and date and reference and facture_numero and montantEncaisse ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    print(facture_numero)

    if Encaissements.query.filter_by(reference=reference).first() is not None:
        return jsonify({'erreur': "Référence d'encaissement existe déja"}), 409



    new_encaissement = Encaissements(modeReglement=modeReglement, date=date,montantEncaisse=montantEncaisse,reference=reference,
       facture_id=facture_numero,
       )
    date_facture = datetime.strptime(get_facture_by_id(facture_numero)[0].json['facture']['date'], '%a, %d %b %Y %H:%M:%S %Z')
    date_encaissement = datetime.strptime(date, '%Y-%m-%d')
    if date_encaissement < date_facture :
        return jsonify({
            "erreur": "Date antérieur à la date de facture"
        }), 400


    db.session.add(new_encaissement)

    # update_facture_result = updateFactureAfterEncaissement(facture_numero, montantEncaisse)
    # if not update_facture_result[0]:
    #     db.session.rollback()  
    #     return update_facture_result[1], 500  

    # db.session.commit()  
    # return make_response(jsonify({"message": "encaissement crée avec succes", "encaissement": new_encaissement.serialize()}), 201)
    update_facture_result, status_code = updateFactureAfterEncaissement(facture_numero, montantEncaisse)
    if not update_facture_result:
        db.session.rollback()  
        return status_code 
    return make_response(jsonify({"message": "encaissement crée avec succes", "encaissement": new_encaissement.serialize()}), 201)


#GetAll encaissement
@encaissement.route('/getAll', methods=['GET'])
@jwt_required()
def get_all_encaissements():
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    if start_date and end_date:
        encaissements = Encaissements.query.filter(Encaissements.date.between(start_date, end_date)).order_by(Encaissements.date.desc()).all()

    for encaissement in encaissements:
        print(f"ID: {encaissement.id}, Date: {encaissement.date}")

    serialized_encaissements = [encaissement.serialize() for encaissement in encaissements]

    return jsonify(serialized_encaissements)



#Updatepaiement
@encaissement.route('/updateEncaissement/<int:id>',methods=['PUT'])
@jwt_required()
def updateEncaissement(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        return jsonify({"message": "encaissement n'existe pas"}), 404

    oldfact=encaissement.facture_id
    oldmontant=encaissement.montantEncaisse

    data = request.get_json()
    print("Received facture_id:", data.get("facture_id"))
    encaissement.date = data.get("date",encaissement.date)
    encaissement.reference = data.get("reference",encaissement.reference)
    encaissement.montantEncaisse = data.get("montantEncaisse",encaissement.montantEncaisse)
    encaissement.modeReglement = data.get("modeReglement",encaissement.modeReglement)
    encaissement.facture_id = data.get("facture_id",encaissement.facture_id)
    
    if encaissement.facture_id is None:
        return jsonify({"message": "Facture ID manquant"}), 400

    update_facture_result, status_code = updateFactureAfterEncaissement(data.get("facture_id"), data.get("montantEncaisse"))
    update_facture_result1, status_code1 = updateFactureAfterCancelEncaissement(oldfact,oldmontant)
    
    if not update_facture_result:
        db.session.rollback()  
        return status_code 
        
    if not update_facture_result1:
        db.session.rollback()  
        return status_code1 
    
    try:
        db.session.commit()
        return jsonify({"message": "encaissement modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de l'encaissement"}), 500
    

#CancelPaiement
@encaissement.route('/cancelEncaissement/<int:id>',methods=['DELETE'])
@jwt_required()
def cancelEncaissement(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        return jsonify({"message": "encaissement n'existe pas"}), 404
    
    update_facture_result1, status_code1 = updateFactureAfterCancelEncaissement(encaissement.facture_id,encaissement.montantEncaisse)
        
    if not update_facture_result1:
        db.session.rollback()  
        return status_code1 
    
    try:
        db.session.delete(encaissement)
        db.session.commit()
        return jsonify({"message": "encaissement annulé avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de l'annulation de l'encaissement"}), 500
  

#generer recu de paiement
@encaissement.route('/recu/<int:encaissement_id>',methods=['GET'])
@jwt_required()
def receipt(encaissement_id):
    encaissement = Encaissements.query.get_or_404(encaissement_id)
    encaissement_data = encaissement.serialize()

    html = render_template('recu_paiement.html', encaissement=encaissement_data)
    
    pdf = weasyprint.HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=recu_encaissement_{encaissement_id}.pdf'

    return response

#GetencaissementByID
@facture.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()
def get_encaissement_by_id(id):
    encaissement = Encaissements.query.get(id)

    if not encaissement:
        
        return jsonify({"message": "encaissement n'existe pas"}), 404

    
    return jsonify({
        'message': "encaissement existe :",
        'encaissement': encaissement.serialize()
    }), 200

