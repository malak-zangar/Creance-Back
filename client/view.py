import io
from flask import Blueprint, Response, request, jsonify, make_response
import pandas as pd
from datetime import date, datetime
from client.model import Users
from db import db
import validators
from flask_jwt_extended import jwt_required


user = Blueprint('user', __name__, url_prefix='/user')

#Add new client
@user.route('/create', methods=['POST'])
@jwt_required()
def create_client():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    emailcc=data.get("emailcc")
    phone = data.get("phone")
    identifiantFiscal=data.get("identifiantFiscal")
    adresse = data.get("adresse")
    dateCreation = data.get("dateCreation")
    delaiRelance = data.get("delaiRelance")
    maxRelance = data.get("maxRelance")

    actif = False

    if not (username and dateCreation and email and phone and adresse and identifiantFiscal and emailcc):
        return jsonify({
            "erreur": "svp entrer toutes les données nécessaires"
        }), 400
    

    if len(username) < 3:
        return jsonify({'erreur': "Nom d'utilisateur trop court"}), 400

    if not validators.email(email) or not validators.email(emailcc):
        return jsonify({'error': "Email is not valid"}), 400

    if Users.query.filter_by(email=email).first() is not None:
        return jsonify({'erreur': "Email existe déja"}), 409

    if Users.query.filter_by(username=username).first() is not None:
        return jsonify({'erreur': "Nom d'utilisateur existe déja"}), 409
    
    if Users.query.filter_by(identifiantFiscal=identifiantFiscal).first() is not None:
        return jsonify({'erreur': "Identifiant fiscal existe déja"}), 409


    new_client = Users(username=username, email=email,phone=phone,adresse=adresse,identifiantFiscal=identifiantFiscal,
                       emailcc=emailcc,actif=actif, dateCreation=dateCreation,delaiRelance=delaiRelance,maxRelance=maxRelance)
    db.session.add(new_client)
    db.session.commit()
    return make_response(jsonify({"message": "client created successfully", "client": new_client.serialize()}), 201)


#GetAll Clients
@user.route('/getAll', methods=['GET'])
@jwt_required()
def get_all_clients():
    clients = Users.query.order_by(Users.dateCreation.desc()).all()
    serialized_clients = [client.serialize() for client in clients]
    return jsonify(serialized_clients)

#GetActifClients
@user.route('/getAllActif', methods=['GET'])
@jwt_required()
def get_all_actif_clients():
    actif_clients = Users.query.filter_by(actif=True).order_by(Users.dateCreation.desc()).all()
    serialized_clients = [client.serialize() for client in actif_clients]
    return jsonify(serialized_clients)

#GetArchivedClients
@user.route('/getAllArchived', methods=['GET'])
@jwt_required()
def get_all_archived_clients():
    archived_clients = Users.query.filter_by(actif=False).order_by(Users.dateCreation.desc()).all()
    serialized_clients = [client.serialize() for client in archived_clients]
    return jsonify(serialized_clients)


#GetClientByID
@user.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()
def get_client_by_id(id):
    client = Users.query.get(id)
    if not client:
        return jsonify({"message": "Client n'existe pas"}), 404

    return jsonify({
        'message': "client existe :",
        'client': client.serialize()
    }), 200


#activerClient
@user.route('/activerClient/<int:id>',methods=['PUT'])
@jwt_required()
def activerClient(id):
    client = Users.query.get(id)

    if not client:
        return jsonify({"message": "client n'existe pas"}), 404
    
    client.actif=True

    try:
        db.session.commit()
        return jsonify({"message": "Client restauré avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans la restauration du client"}), 500


#UpdateClient
@user.route('/updateClient/<int:id>',methods=['PUT'])
@jwt_required()
def updateClient(id):
    client = Users.query.get(id)

    if not client:
        return jsonify({"message": "client n'existe pas"}), 404
    
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
    client.username = data.get('username', client.username)
    client.email = data.get('email', client.email)
    client.phone = data.get('phone', client.phone)
    client.adresse = data.get('adresse', client.adresse)
    client.actif = data.get('actif',client.actif)
    client.emailcc=data.get('emailcc',client.emailcc)
    client.identifiantFiscal= data.get('identifiantFiscal', client.identifiantFiscal)
    client.dateCreation= parse_date(data.get("dateCreation",client.dateCreation))
    client.delaiRelance = data.get('delaiRelance',client.delaiRelance)
    client.maxRelance = data.get('maxRelance',client.maxRelance)

    try:
        db.session.commit()
        return jsonify({"message": "Client modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification du client"}), 500

@user.route('/export/csv/actifusers', methods=['GET'])
@jwt_required()
def export_csv_actifusers():
    try:
        columns = request.args.get('columns')
        if columns:
            columns = columns.split(',')
        else:
            columns = ['username','email', 'emailcc', ]  # Default columns

        users = Users.query.filter_by(actif=True).all()
        users_list = [user.serialize_for_export() for user in users]
        for col in columns:
            if col not in users_list[0]:
                return Response(
                    f"Column '{col}' does not exist in user data",
                    status=400
                )

        filtered_users_list = [{col: user[col] for col in columns} for user in users_list]
        
        df = pd.DataFrame(filtered_users_list)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=actifusers.csv"}
        )
    except Exception as e:
        return Response(
            f"Internal Server Error: {str(e)}",
            status=500
        )


    #export to csv

@user.route('/export/csv/nonactif',methods=['GET'])
@jwt_required()
def export_csv_nonactifusers():
    try :
        columns = request.args.get('columns')
        if columns:
            columns = columns.split(',')
        else:
            columns = ['username','email', 'emailcc', ]  # Default columns

        users = Users.query.filter_by(actif=False).all()
        users_list = [user.serialize_for_export() for user in users]
        for col in columns:
            if col not in users_list[0]:
                return Response(
                    f"Column '{col}' does not exist in user data",
                    status=400
                )

        filtered_users_list = [{col: user[col] for col in columns} for user in users_list]
        
        df = pd.DataFrame(filtered_users_list)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=actifusers.csv"}
              )
    except Exception as e:
        return jsonify({"error": str(e)}), 500