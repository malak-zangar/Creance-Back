import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


class Config :
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv("SECRET_KEY")

    TARGET_CURRENCY='EUR' 

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_size' : 100, 'pool_recycle' : 300, "pool_pre_ping": True}

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587  
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") 