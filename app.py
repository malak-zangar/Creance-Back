from datetime import timedelta
from flask import Flask
import logging
from flask_cors import CORS
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager
from apscheduler.triggers.cron import CronTrigger
from flask_jwt_extended import JWTManager
from auth.model import Auth
from client.view import user
from facture.view import facture, retard_counter, schedule_reminders
from encaissement.view import encaissement
from contrat.view import contrat
from paramEntreprise.view import paramentreprise
from dashboard.view import dashboard
from relance.view import emailcascade
from db import db
from config import Config


app = Flask(__name__, static_folder='static')
CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173", "supports_credentials": True}})

app.config.from_object(Config)

from flask_mail import Mail

mail = Mail(app)

db.init_app(app)

app.register_blueprint(user)
app.register_blueprint(facture)
app.register_blueprint(encaissement)
app.register_blueprint(contrat)
app.register_blueprint(paramentreprise)
app.register_blueprint(dashboard)
app.register_blueprint(emailcascade)

jwt = JWTManager(app)

login_manager = LoginManager()
login_manager.init_app(app)

from auth.view import auth
app.register_blueprint(auth)

@app.before_first_request
def create_tables():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Auth.query.get(int(user_id))


handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

scheduler = BackgroundScheduler()
scheduler.add_job(func=retard_counter, trigger=CronTrigger(hour=00, minute=00))
scheduler.add_job(func=schedule_reminders, trigger=CronTrigger(hour=18, minute=3))
scheduler.start()

with app.app_context():
    retard_counter()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
