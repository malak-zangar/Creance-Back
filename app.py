from datetime import datetime, time, timedelta
import os

import pytz
from auth.model import Auth
from db import db
from flask import Flask, current_app
import logging
from flask_cors import CORS
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager
from apscheduler.triggers.cron import CronTrigger
from user.view import user
from facture.view import facture, schedule_reminders
from encaissement.view import encaissement

load_dotenv(dotenv_path=".env")

app = Flask(__name__)

CORS(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size' : 100, 'pool_recycle' : 300,"pool_pre_ping": True}


# Configuration de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # ou 465 pour SSL
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

from flask_mail import Mail, Message

mail = Mail(app)


db.init_app(app)

app.register_blueprint(user)
app.register_blueprint(facture)
app.register_blueprint(encaissement)


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

#scheduler = BackgroundScheduler()
#scheduler.add_job(func=schedule_reminders, trigger="interval", days=1)
#scheduler.add_job(func=schedule_reminders, trigger=CronTrigger(hour=11, minute=0))

# Définir l'heure à laquelle vous voulez que la tâche soit exécutée
#scheduled_time = time(hour=11, minute=0)

# Ajouter la tâche avec un déclencheur interval quotidien à l'heure spécifiée
#scheduler.add_job(func=schedule_reminders, trigger="interval", days=1, start_date=datetime.now(), time=scheduled_time)


# Définir l'heure à laquelle vous voulez que la tâche soit exécutée
#scheduled_time = '0 11 * * *'  # À 11h00 chaque jour

# Ajouter la tâche avec un déclencheur Cron pour 11h00 chaque jour
#scheduler.add_job(func=schedule_reminders, trigger=CronTrigger.from_crontab(scheduled_time))


#scheduler.start()


scheduler = BackgroundScheduler()
#scheduled_time = datetime.now(pytz.utc).replace(hour=10, minute=30, second=0, microsecond=0)
#delta_time = scheduled_time - datetime.now(pytz.utc)
#scheduler.add_job(func=schedule_reminders, trigger='date', run_date=datetime.now() + delta_time)

# Définir l'heure à laquelle vous voulez que la tâche soit exécutée (à 11h00 UTC)
#scheduled_time = datetime.now(pytz.utc).replace(hour=10, minute=38, second=0, microsecond=0)

# Ajouter la tâche avec un déclencheur Cron pour 11h00 chaque jour
scheduler.add_job(func=schedule_reminders, trigger=CronTrigger(hour=10, minute=45))
scheduler.start()

with app.app_context():
    schedule_reminders()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")

