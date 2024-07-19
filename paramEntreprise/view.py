from flask import Blueprint, Response, request, jsonify, make_response
from datetime import datetime, timedelta
from db import db
import validators
from flask_jwt_extended import jwt_required

from paramEntreprise.model import ParamEntreprise


paramentreprise = Blueprint('paramentreprise', __name__, url_prefix='/paramentreprise')

#Add new paramentreprise
@paramentreprise.route('/create', methods=['POST'])
@jwt_required()
def create_paramentrep():

    today = datetime.today()

    data = request.get_json()
    raisonSociale = data.get("raisonSociale")
    email = data.get("email")
    phone = data.get("phone")
    identifiantFiscal=data.get("identifiantFiscal")
    adresse = data.get("adresse")
    dateInsertion = today.strftime('%Y-%m-%d')

    if not (dateInsertion and raisonSociale and email and phone and adresse and identifiantFiscal ):
        return jsonify({
            "erreur": "svp entrer toutes les données nécessaires"
        }), 400
    

    if len(raisonSociale) < 3:
        return jsonify({'erreur': "Raison sociale  trop courte"}), 400

    if not validators.email(email) :
        return jsonify({'error': "Email is not valid"}), 400


    new_paramentrep = ParamEntreprise(raisonSociale=raisonSociale, email=email,phone=phone,adresse=adresse,identifiantFiscal=identifiantFiscal,
                      dateInsertion=dateInsertion)
    db.session.add(new_paramentrep)
    db.session.commit()
    return make_response(jsonify({"message": "paramentreprise created successfully", "paramentreprise": new_paramentrep.serialize()}), 201)


#GetAll paramentreps
@paramentreprise.route('/getAll', methods=['GET'])
@jwt_required()
def get_all_paramentreps():
    paramentreps = ParamEntreprise.query.order_by(ParamEntreprise.dateInsertion.desc()).all()
    serialized_paramentreps = [paramentreprise.serialize() for paramentreprise in paramentreps]
    return jsonify(serialized_paramentreps)


#GetparamentrepByID
@paramentreprise.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()

def get_paramentrep_by_id(id):
    paramentreprise = ParamEntreprise.query.get(id)

    if not paramentreprise:
        return jsonify({"message": "paramentreprise n'existe pas"}), 404

    return jsonify({
        'message': "paramentreprise existe :",
        'paramentreprise': paramentreprise.serialize()
    }), 200

# Update paramentrep
@paramentreprise.route('/updateparamentrep/<int:id>', methods=['PUT'])
@jwt_required()
def updateparamentrep(id):
    existing_paramentreprise = ParamEntreprise.query.get(id)

    if not existing_paramentreprise:
        return jsonify({"message": "paramentreprise n'existe pas"}), 404
    
    data = request.get_json()
    raisonSociale = data.get('raisonSociale', existing_paramentreprise.raisonSociale)
    email = data.get('email', existing_paramentreprise.email)
    phone = data.get('phone', existing_paramentreprise.phone)
    adresse = data.get('adresse', existing_paramentreprise.adresse)
    identifiantFiscal = data.get('identifiantFiscal', existing_paramentreprise.identifiantFiscal)
    dateInsertion = datetime.today().strftime('%Y-%m-%d')

    new_paramentreprise = ParamEntreprise(
        raisonSociale=raisonSociale,
        email=email,
        phone=phone,
        adresse=adresse,
        identifiantFiscal=identifiantFiscal,
        dateInsertion=dateInsertion
    )

    try:
        db.session.add(new_paramentreprise)
        db.session.commit()
        return jsonify({"message": "paramentreprise modifié avec succès", "paramentreprise": new_paramentreprise.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification du paramentreprise"}), 500

# Get the latest paramentrep
@paramentreprise.route('/getLatest', methods=['GET'])
@jwt_required()
def get_latest_paramentrep():
    latest_paramentreprise = ParamEntreprise.query.order_by(ParamEntreprise.dateInsertion.desc()).first()
    
    if not latest_paramentreprise:
        return jsonify({"message": "Aucun paramentreprise trouvé"}), 404

    return jsonify({
        'message': "Dernier paramentreprise trouvé :",
        'paramentreprise': latest_paramentreprise.serialize()
    }), 200