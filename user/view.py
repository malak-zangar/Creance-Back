from flask import Blueprint, request, jsonify, make_response, redirect, flash, render_template
from datetime import datetime, timedelta
from user.model import Users
from db import db
import validators

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/register', methods=['POST'])
def register():
    # Code to register a user
    return make_response(jsonify({"message": "User created successfully"}), 201)

@user.route('/login', methods=['POST'])
def login():
    # Code to login a user
    return make_response(jsonify({"message": "User logged in successfully"}), 200)


#Add new client
@user.route('/create', methods=['POST'])
def create_client():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone")
    adresse = data.get("adresse")
    actif = True

    if not (username and email and phone and adresse):
        return jsonify({
            "erreur": "svp entrer un nom d'utilisateur, un email , un numéro de téléphone et une adresse"
        }), 400
    

    if len(username) < 3:
        return jsonify({'erreur': "Nom d'utilisateur trop court"}), 400

    if not username.isalnum() or " " in username:
        return jsonify({'erreur': "nom d'utilisateur ne doit contenir que des caractères et pas d'espace "}), 400

    if not validators.email(email):
        return jsonify({'error': "Email is not valid"}), 400

    if Users.query.filter_by(email=email).first() is not None:
        return jsonify({'erreur': "Email iexiste déja"}), 409

    if Users.query.filter_by(username=username).first() is not None:
        return jsonify({'erreur': "Nom d'utilisateur existe déja"}), 409
    
    if Users.query.filter_by(phone=phone).first() is not None:
        return jsonify({'erreur': "Numéro de téléphone existe déja"}), 409


    new_client = Users(username=username, email=email,phone=phone,adresse=adresse,actif=actif)
    db.session.add(new_client)
    db.session.commit()
    return make_response(jsonify({"message": "client created successfully", "client": new_client.serialize()}), 201)


#GetAll Clients
@user.route('/getAll', methods=['GET'])
def get_all_clients():
    #return list(map(lambda x: x.serialize(), Users.query.all()))
    clients = Users.query.all()
    serialized_clients = [client.serialize() for client in clients]
    return jsonify(serialized_clients)

#GetActifClients
@user.route('/getAllActif', methods=['GET'])
def get_all_actif_clients():
    actif_clients = Users.query.filter_by(actif=True).all()
    serialized_clients = [client.serialize() for client in actif_clients]
    return jsonify(serialized_clients)
    #return list(map(lambda x: x.serialize(), actif_clients))

#GetArchivedClients
@user.route('/getAllArchived', methods=['GET'])
def get_all_archived_clients():
    archived_clients = Users.query.filter_by(actif=False).all()
    serialized_clients = [client.serialize() for client in archived_clients]
    return jsonify(serialized_clients)
    #return list(map(lambda x: x.serialize(), archived_clients))


#GetClientByID
@user.route('/getByID/<int:id>',methods=['GET'])
def get_client_by_id(id):
    client = Users.query.get(id)

    if not client:
        
        return jsonify({"message": "Client n'existe pas"}), 404

    
    return jsonify({
        'message': "client existe :",
        'client': client.serialize()
    }), 200

#ArchiveClient
@user.route('/archiveClient/<int:id>',methods=['PUT'])
def archiverClient(id):
    client = Users.query.get(id)

    if not client:
        return jsonify({"message": "client n'existe pas"}), 404
    
    client.actif=False

    try:
        db.session.commit()
        return jsonify({"message": "Client archivé avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans l'archivage du client"}), 500
    

#UpdateClient
@user.route('/updateClient/<int:id>',methods=['PUT'])
def updateClient(id):
    client = Users.query.get(id)

    if not client:
        return jsonify({"message": "client n'existe pas"}), 404
    
    data = request.get_json()
    client.username = data.get('username', client.username)
    client.email = data.get('email', client.email)
    client.phone = data.get('phone', client.phone)
    client.adresse = data.get('adresse', client.adresse)
    client.actif = data.get('actif',client.actif)

    try:
        db.session.commit()
        return jsonify({"message": "Client modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification du client"}), 500

