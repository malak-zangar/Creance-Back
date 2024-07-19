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
    delai = int(data.get("delai"))
    conditionsFinancieres = data.get("conditionsFinancieres")
    prochaineAction = data.get("prochaineAction")
    dateProchaineAction = data.get("dateProchaineAction")
    dateRappel = data.get("dateRappel")
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


    if not (reference and dateDebut and delai and client_id ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    
    try:
        date = datetime.strptime(dateDebut, '%Y-%m-%d')
        dateFin = date + timedelta(days=int(delai))

    except ValueError:
        return jsonify({
            "erreur": "Format de date ou délai invalide"
        }), 400

     
    if Contrats.query.filter_by(reference=reference).first() is not None:
        return jsonify({'erreur': "Référence de contrat existe déja"}), 409
    
    response = activer_client(token, client_id)
    if response.status_code != 200:
        return jsonify({
            "erreur": "Échec dans l'activation du client"
        }), 500

    print(data)
    new_contrat = Contrats(reference=reference, dateDebut=dateDebut,dateFin=dateFin,delai=delai,
                client_id=client_id,conditionsFinancieres=conditionsFinancieres,prochaineAction=prochaineAction,
                dateProchaineAction=dateProchaineAction,dateRappel=dateRappel,paramentrep_id=paramentrep_id  )
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
    contrat.reference = data.get("reference",contrat.reference)
    contrat.dateDebut= parse_date(data.get("dateDebut",contrat.dateDebut))
    contrat.conditionsFinancieres = data.get("conditionsFinancieres",contrat.conditionsFinancieres)
    contrat.delai = data.get("delai",contrat.delai)
    contrat.dateProchaineAction= parse_date(data.get("dateProchaineAction",contrat.dateProchaineAction))
    contrat.dateRappel = parse_date(data.get("dateRappel",contrat.dateRappel)) 
    contrat.prochaineAction = data.get("prochaineAction",contrat.prochaineAction)
    try:
        contrat.dateFin = contrat.dateDebut + timedelta(days=int(contrat.delai))

    except ValueError:
        return jsonify({
            "erreur": "Format de date ou délai invalide"
        }), 400

    try:
        db.session.commit()
        return jsonify({"message": "contrat modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification du contrat"}), 500
    


@contrat.route('/report/<int:contrat_id>',methods=['GET'])
@jwt_required()

def report(contrat_id):
    contrat = Contrats.query.get_or_404(contrat_id)
    contrat_data = contrat.serialize()


    html = render_template('contrat_report.html', contrat=contrat_data)
    
    pdf = weasyprint.HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=report_contrat_{contrat_id}.pdf'

    return response