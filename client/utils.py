from flask import jsonify
from client.model import Users


def get_client_by_id(id):
    client = Users.query.get(id)
    if not client:
        return jsonify({"message": "Client n'existe pas"}), 404

    return jsonify({
        'message': "client existe :",
        'client': client.serialize()
    }), 200