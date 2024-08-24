from flask import jsonify
import requests

from contrat.model import Contrats

def get_contrat_by_id(id):
    contrat = Contrats.query.get(id)

    if not contrat:
        return jsonify({"message": "contrat n'existe pas"}), 404

    return jsonify({
        'message': "contrat existe :",
        'contrat': contrat.serialize()
    }), 200


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