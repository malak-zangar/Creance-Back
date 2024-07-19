from datetime import timedelta
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from auth.model import Auth
from jwt.exceptions import ExpiredSignatureError  # Import from jwt.exceptions
from db import db

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
        access_token = create_access_token(identity=user.username, expires_delta=timedelta(hours=2))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"erreur": "Invalid username or password"}), 401

# Add new admin
@auth.route('/create', methods=['POST'])
def create_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not (username and password):
        return jsonify({
            "erreur": "svp entrer un nom d'utilisateur et mot de passe"
        }), 400
    
    if len(username) < 3:
        return jsonify({'erreur': "Nom d'utilisateur trop court"}), 400

    if not username.isalnum() or " " in username:
        return jsonify({'erreur': "nom d'utilisateur ne doit contenir que des caractères et pas d'espace "}), 400

    new_admin = Auth(username=username, password=generate_password_hash(password, method='sha256'))
    db.session.add(new_admin)
    db.session.commit()
    return make_response(jsonify({"message": "admin created successfully", "admin": new_admin.serialize()}), 201)

@auth.route("/logout", methods=['POST'])
@jwt_required()
def logout():
    return 'user logged out successfully'

@auth.route("/protected", methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify(logged_in_as=current_user_id), 200
