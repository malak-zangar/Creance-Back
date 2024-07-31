import base64
from logging import log
from flask import Blueprint, current_app, render_template, request, jsonify, make_response 
from datetime import date, datetime, timedelta
import weasyprint 
from contrat.model import Contrats
from db import db
from user.view import *
from sqlalchemy import cast, Integer 
import requests  
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity 
from paramEntreprise.view import *


contrat = Blueprint('contrat', __name__, url_prefix='/contrat')


def activer_client(token, client_id):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    url = f"http://localhost:5555/user/activerClient/{client_id}"
    response = requests.put(url, headers=headers)
    return response

def get_latest_paramentreprise(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get('http://localhost:5555/paramentreprise/getLatest', headers=headers)
    if response.status_code == 200:
        return response.json().get('paramentreprise', {}).get('id')
    return None

#Add new contrat
@contrat.route('/create', methods=['POST'])
@jwt_required()
def create_contrat():
    data = request.get_json()
    reference = data.get("reference")
    dateDebut = data.get("dateDebut")
    dateFin = data.get("dateFin")
    delai = int(data.get("delai"))
    devise = data.get("devise")
    type = data.get("type")
    total = data.get("total")
    prixJourHomme = data.get("prixJourHomme")
    typeFrequenceFacturation = data.get("typeFrequenceFacturation")   
    detailsFrequence=data.get("detailsFrequence")
    montantParMois=data.get("montantParMois")
    contratFile = data.get('contratFile')
    client_id = int(data.get("client_id"))

 # Extract the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return jsonify({"erreur": "Token d'authentification manquant"}), 401

    paramentrep_id = get_latest_paramentreprise(token)
    if paramentrep_id is None:
        return jsonify({"erreur": "Erreur lors de la récupération du dernier paramentreprise"}), 500

    

    if delai < 1 :
        return jsonify({
            "erreur": "le délai doit etre au moins égal à 1 jour"
        }), 400
    
    if dateDebut>dateFin :
        return jsonify({
            "erreur": "la date de fin doit etre supérieur à la date de début"
        }), 400

    if not (reference and type and typeFrequenceFacturation and devise and dateFin and dateDebut and delai and client_id ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    


     
    if Contrats.query.filter_by(reference=reference).first() is not None:
        return jsonify({'erreur': "Référence de contrat existe déja"}), 409
    
    response = activer_client(token, client_id)
    if response.status_code != 200:
        return jsonify({
            "erreur": "Échec dans l'activation du client"
        }), 500

    print(data)

    pdf_file = None
    if contratFile:
        pdf_file = base64.b64decode(contratFile)


    new_contrat = Contrats(reference=reference,devise=devise, dateDebut=dateDebut,dateFin=dateFin,delai=delai,contratFile=pdf_file,
                client_id=client_id,type=type,total=total,prixJourHomme=prixJourHomme,typeFrequenceFacturation=typeFrequenceFacturation,
                detailsFrequence=detailsFrequence,montantParMois=montantParMois,paramentrep_id=paramentrep_id  )
    print(new_contrat)
    db.session.add(new_contrat)
    db.session.commit()
    return make_response(jsonify({"message": "contrat crée avec succes", "contrat": new_contrat.serialize()}), 201)


#GetAll contrats
@contrat.route('/getAll', methods=['GET'])
@jwt_required()
def get_all_contrats():
    contrats = Contrats.query.order_by(Contrats.dateDebut.desc()).all()
    serialized_contrats = [contrat.serialize() for contrat in contrats]
    return make_response(jsonify(serialized_contrats))

# Get contracts where end date is less than the current date
@contrat.route('/getExpired', methods=['GET'])
@jwt_required()
def get_expired_contrats():
    current_date = datetime.now().date()
    expired_contrats = Contrats.query.filter(Contrats.dateFin < current_date).order_by(Contrats.dateFin.desc()).all()
    if not expired_contrats:
        return jsonify({"message": "Aucun contrat expiré trouvé"}), 404

    serialized_expired_contrats = [contrat.serialize() for contrat in expired_contrats]
   # return jsonify({"message": "Contrats expirés trouvés", "contracts": serialized_expired_contrats}), 200
    return make_response(jsonify(serialized_expired_contrats))

# GetcontractsActif
@contrat.route('/getActif', methods=['GET'])
@jwt_required()
def get_actif_contrats():
    current_date = datetime.now().date()
    actif_contrats = Contrats.query.filter(Contrats.dateFin >= current_date).order_by(Contrats.dateFin.desc()).all()
    if not actif_contrats:
        return jsonify({"message": "Aucun contrat actif trouvé"}), 404

    serialized_due_today_contrats = [contrat.serialize() for contrat in actif_contrats]
   # return jsonify({"message": "Contrats actifs trouvés", "contracts": serialized_due_today_contrats}), 200
    return make_response(jsonify(serialized_due_today_contrats))



#GetContratByID
@contrat.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()
def get_contrat_by_id(id):
    contrat = Contrats.query.get(id)

    if not contrat:
        return jsonify({"message": "contrat n'existe pas"}), 404

    return jsonify({
        'message': "contrat existe :",
        'contrat': contrat.serialize()
    }), 200

#GetcontratByreference
@contrat.route('/getByReference/<string:reference>',methods=['GET'])
@jwt_required()
def get_contrat_by_reference(reference):
    contrat = Contrats.query.filter(cast(reference, Integer) == reference).first()

    if not contrat:
        return jsonify({"message": "contrat n'existe pas"}), 404

    return jsonify({
            'message': "contrat existe :",
            'contrat': contrat.serialize(),
        }), 200


#GetcontratByclient
@contrat.route('/getByClient/<int:id>',methods=['GET'])
@jwt_required()
def get_contrat_by_client(id):
    contracts = Contrats.query.filter_by(client_id=id).order_by(Contrats.dateDebut.desc()).all()

    if not contracts:
        return jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404

    serialized_contracts = [contrat.serialize() for contrat in contracts]
    return jsonify({"message": "Contrats trouvés pour le client", "contracts": serialized_contracts}), 200
 
#GetActualcontratByclient
@contrat.route('/getActualByClient/<int:id>',methods=['GET'])
@jwt_required()
def get_actual_contrat_by_client(id):
    current_date = datetime.now().date()
    contracts = Contrats.query.filter(Contrats.client_id == id,Contrats.dateDebut <= current_date, Contrats.dateFin >= current_date).order_by(Contrats.dateDebut.desc()).all()

    if not contracts:
        return jsonify({"message": "Aucun contrat actuel trouvé pour ce client"}), 404

    serialized_contracts = [contrat.serialize() for contrat in contracts]
    return jsonify({"message": "Contrats actuels trouvés pour le client", "contracts": serialized_contracts}), 200


#UpdateContrat
@contrat.route('/updateContrat/<int:id>',methods=['PUT'])
@jwt_required()
def updateContrat(id):
    contrat = Contrats.query.get(id)

    if not contrat:
        return jsonify({"message": "contrat n'existe pas"}), 404
    def parse_date(date_input):
        if isinstance(date_input, str):
            try:
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid date format")
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, date):
            return date_input
        else:
            raise ValueError("Invalid date format")

    data = request.get_json()
    contratFile = data.get('contratFile')
    contrat.reference = data.get("reference",contrat.reference)
    contrat.dateDebut= parse_date(data.get("dateDebut",contrat.dateDebut))
    contrat.dateFin= parse_date(data.get("dateFin",contrat.dateFin))
    contrat.delai = data.get("delai",contrat.delai)
    contrat.devise = data.get("devise",contrat.devise)
    contrat.type = data.get("type")
    contrat.total = data.get("total")
    contrat.prixJourHomme = data.get("prixJourHomme")
    contrat.typeFrequenceFacturation = data.get("typeFrequenceFacturation")
    contrat.detailsFrequence = data.get("detailsFrequence")
    contrat.montantParMois = data.get("montantParMois")
    

    if contratFile:
        contrat.contratFile = base64.b64decode(contratFile)


    try:
        db.session.commit()
        return jsonify({"message": "contrat modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification du contrat"}), 500
    


@contrat.route('/contratFile/<int:contrat_id>/<string:reference>',methods=['GET'])
@jwt_required()
def report(contrat_id,reference):
    
    contrat = Contrats.query.get(contrat_id)
    if not contrat or not contrat.contratFile:
        return jsonify({"message": "PDF non trouvé pour ce contrat"}), 404

    response = make_response(contrat.contratFile)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=contrat_{reference}.pdf'

    return response