from flask import Blueprint, flash, redirect, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
from auth.model import Auth
from db import db

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        user = Auth.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            #next_page = request.args.get('next')
            return "admin logged in"
        else:
            return "Invalid username or password"


#Add new admin
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



@auth.route("/logout")
def logout():
    logout_user()
    return 'user logged out successfully'