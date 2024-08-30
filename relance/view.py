import os
from flask import Blueprint, request, jsonify, make_response
from datetime import date, datetime
from db import db
from flask_jwt_extended import jwt_required
from relance.model import EmailCascade


emailcascade = Blueprint('emailcascade', __name__, url_prefix='/emailcascade')

#Add new email
@emailcascade.route('/create', methods=['POST'])
@jwt_required()
def create_email():

    today = datetime.today()

    data = request.get_json()
    objet = data.get("objet")
    corps = data.get("corps")
    type = data.get("type")
    dateInsertion = today.strftime('%Y-%m-%d')


    if not (dateInsertion and objet and corps and type):
        return jsonify({
            "erreur": "svp entrer toutes les données nécessaires"
        }), 400
    

    if len(objet) < 3 :
        return jsonify({'erreur': "objet d'email trop court"}), 400
    if len(corps) < 50 :
        return jsonify({'erreur': "Corps d'email trop court"}), 400
    if len(type) < 5:
        return jsonify({'erreur': "Type d'email trop court"}), 400

    new_emailcascade = EmailCascade(objet=objet,corps=corps,type=type, dateInsertion=dateInsertion)
    db.session.add(new_emailcascade)
    db.session.commit()
    return make_response(jsonify({"message": "emailcascade created successfully", "emailcascade": new_emailcascade.serialize()}), 201)


#GetAll emailcascade
@emailcascade.route('/getAll', methods=['GET'])
@jwt_required()
def get_all_emailcascades():
    emailcascades = EmailCascade.query.order_by(EmailCascade.dateInsertion.desc()).all()
    serialized_emailcascades = [emailcascade.serialize() for emailcascade in emailcascades]
    return jsonify(serialized_emailcascades)


#GetemailcascadeByID
@emailcascade.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()
def get_emailcascade_by_id(id):
    emailcascade = EmailCascade.query.get(id)

    if not emailcascade:
        return jsonify({"message": "emailcascade n'existe pas"}), 404

    return jsonify({
        'message': "emailcascade existe :",
        'emailcascade': emailcascade.serialize()
    }), 200

# Update emailcascade
@emailcascade.route('/updateemailcascade/<int:id>', methods=['PUT'])
@jwt_required()
def updateemailcascade(id):
    existing_emailcascade = EmailCascade.query.get(id)

    if not existing_emailcascade:
        return jsonify({"message": "emailcascade n'existe pas"}), 404
    
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
    existing_emailcascade.objet = data.get('objet', existing_emailcascade.objet)
    existing_emailcascade.corps = data.get('corps', existing_emailcascade.corps)
    existing_emailcascade.type = data.get('type', existing_emailcascade.type)
    existing_emailcascade.dateInsertion= parse_date(data.get("dateInsertion",existing_emailcascade.dateInsertion))

    try:
        db.session.commit()
        return jsonify({"message": "emailcascade modifié avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de l'emailcascade"}), 500