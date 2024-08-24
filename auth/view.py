from datetime import timedelta
import os
from flask import Blueprint, current_app, request, jsonify, make_response
from flask_mail import Message
import jwt
import validators
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from auth.model import Auth
from jwt.exceptions import ExpiredSignatureError  # Import from jwt.exceptions
from db import db
from paramEntreprise.model import ParamEntreprise
from relance.model import EmailCascade

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.errorhandler(ExpiredSignatureError)
def handle_expired_token_error(error):
    return jsonify({'message': 'Token expiré, reconnectez-vous SVP.'}), 401



@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = Auth.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity={'id': user.id, 'username': user.username}, expires_delta=timedelta(hours=2))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email' : user.email
            }
        }), 200
    else:
        return jsonify({"erreur": "Invalid username or password"}), 402

@auth.route('/getAll', methods=['GET'])
@jwt_required()
def getAll():
    admins = Auth.query.all()
    
    serialized_admins = [admin.serialize() for admin in admins]

    return jsonify(serialized_admins)


# Add new admin
@auth.route('/create', methods=['POST'])
def create_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not (username and password and email):
        return jsonify({
            "erreur": "svp entrer un nom d'utilisateur , un email et un mot de passe"
        }), 400
    
    if len(username) < 3:
        return jsonify({'erreur': "Nom d'utilisateur trop court"}), 400

    if not username.isalnum() :
        return jsonify({'erreur': "nom d'utilisateur ne doit contenir que des caractères"}), 400
    
    if Auth.query.filter_by(username=username).first() is not None:
        return jsonify({'erreur': "Nom d'utilisateur existe déja"}), 409
    
    if not validators.email(email) :
        return jsonify({'error': "Email is not valid"}), 400
    
    if Auth.query.filter_by(email=email).first() is not None:
        return jsonify({'erreur': "Email existe déja"}), 409



    new_admin = Auth(username=username,email=email, password=generate_password_hash(password, method='sha256'))
    db.session.add(new_admin)
    db.session.commit()
    return make_response(jsonify({"message": "admin created successfully", "admin": new_admin.serialize()}), 201)

@auth.route("/logout", methods=['POST'])
@jwt_required()
def logout():
    return 'user logged out successfully'

# @auth.route("/protected", methods=['GET'])
# @jwt_required()
# def protected():
#     current_user_id = get_jwt_identity()
#     return jsonify(logged_in_as=current_user_id), 200


#ModifierProfil
@auth.route('/profile/<int:id>',methods=['PUT'])
@jwt_required()
def updateProfil(id):
    user = Auth.query.get(id)

    if not user:
        return jsonify({"message": "user n'existe pas"}), 404
    data = request.get_json()
    print(data)
    password = data.get("password")
    user.email = data.get("email",user.email)
    user.username = data.get("username",user.username)

    if password : 
        user.password = generate_password_hash(password, method='sha256')

    try:
        db.session.commit()
        return jsonify({"message": "Utilisateur modifié avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans la modification de l'utilisateur "}), 500

#updatePassword
@auth.route('/resetpassword',methods=['PUT'])
def resetPassword():
    data = request.get_json()
    print(data)
    token = data.get('token')
    print(token)
    password = data.get('password')
    print(password)
   

    if not token:
        return jsonify({"message": "Token invalide ou expiré"}), 402
    if not password:
        return jsonify({"message": "Mot de passe requis"}), 400


    try:
        decoded_data = jwt.decode(token, key=os.getenv('SECRET_KEY'), algorithms=["HS256"])
        username = decoded_data['reset_password']

        # Trouvez l'utilisateur par son nom d'utilisateur
        user = Auth.query.filter_by(username=username).first()
        if not user:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
        user.password = generate_password_hash(password, method='sha256')



        db.session.commit()
        return jsonify({"message": "Mot de passe réinitialisé avec succés"}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Le token a expiré"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Token invalide"}), 400
    except Exception as e:
        print(f"Erreur: {e}")
        db.session.rollback()
        return jsonify({"message": "Echec dans la réinitalisation du mot de passe "}), 500

#SendRecuperationMail
@auth.route('/sendmail',methods=['POST'])
def send_recuperation_email():
    from app import mail
    data = request.get_json()
    print(data)

    email=data.get("email")
    if not email:
        return jsonify({"message": "Adresse email manquante"}), 400
    print(email)

    auth=Auth.query.filter_by(email=email).first()

    entrep_param = get_latest_paramentrep()['param_entreprise']
    email_param = EmailCascade.query.filter_by(type='Recepuration de mot de passe').first()

    if auth :
        token = auth.get_reset_token()
        reset_url = f"http://localhost:5173/resetPassword?token={token}"

        subject = email_param.objet
        body = email_param.corps.replace("[Nom d'utilisateur]", auth.username) \
                    .replace("[lien]", reset_url) \
                    .replace("[Nom de l'entreprise]", entrep_param['raisonSociale'])

        try : 
            msg = Message(
                subject,
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            # msg.body = f"Bonjour Monsieur/Madame {auth.username}, veuillez cliquer sur ce lien pour réinitialiser votre mot de passe : {reset_url}"               
            msg.body = body
            mail.send(msg)
            return jsonify({"message": "Email envoyé avec succès"}), 200
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")
            return jsonify({"erreur": "Échec de l'envoi de l'email"}), 500
    else :
        return jsonify({"erreur": "Adresse email n'existe pas"}), 402

@auth.route('/verify-password/<int:id>', methods=['POST'])
@jwt_required()
def verify_password(id):
    data = request.get_json()
    current_password = data.get('password')

    user = Auth.query.get(id)
    if not user or not check_password_hash(user.password, current_password):
        return jsonify({"message": "Mot de passe incorrect"}), 402

    return jsonify({"message": "Mot de passe correct"}), 200

def get_latest_paramentrep():
    latest_paramentreprise = ParamEntreprise.query.order_by(ParamEntreprise.dateInsertion.desc()).first()
    
    if not latest_paramentreprise:
        return jsonify({"message": "Aucun paramentreprise trouvé"}), 404

    return {'param_entreprise': latest_paramentreprise.serialize()}