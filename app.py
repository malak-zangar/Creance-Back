import os
from db import db
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")

app = Flask(__name__)

CORS(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size' : 100, 'pool_recycle' : 300,"pool_pre_ping": True}

db.init_app(app)




@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")

