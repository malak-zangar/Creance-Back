from flask import jsonify

from contrat.model import Contrats
from db import db

def get_contrat_by_id(id):
    contrat = Contrats.query.get(id)

    if not contrat:
        return jsonify({"message": "contrat n'existe pas"}), 404

    return jsonify({
        'message': "contrat existe :",
        'contrat': contrat.serialize()
    }), 200


def activer_client(token, client_id):
    from client.model import Users

    headers = {
        'Authorization': f'Bearer {token}'
    }
    client = Users.query.get(client_id)

    if not client:
        return jsonify({"message": "client n'existe pas"}), 404
    
    client.actif=True

    try:
        db.session.commit()
        return jsonify({"message": "Client restauré avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans la restauration du client"}), 500


def get_latest_paramentreprise(token):
    from paramEntreprise.model import ParamEntreprise

    headers = {
        'Authorization': f'Bearer {token}'
    }

    latest_paramentreprise = ParamEntreprise.query.order_by(ParamEntreprise.dateInsertion.desc()).first()
    
    if not latest_paramentreprise:
        return jsonify({"message": "Aucun paramentreprise trouvé"}), 404

    response= jsonify({
        'message': "Dernier paramentreprise trouvé :",
        'paramentreprise': latest_paramentreprise.serialize()
    }), 200


    if response :
        return latest_paramentreprise.id
    return None