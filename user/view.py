from flask import Blueprint, request, jsonify, make_response, redirect, flash, render_template
from datetime import datetime, timedelta
from user.model import Users
from db import db

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/register', methods=['POST'])
def register():
    # Code to register a user
    return make_response(jsonify({"message": "User created successfully"}), 201)

@user.route('/login', methods=['POST'])
def login():
    # Code to login a user
    return make_response(jsonify({"message": "User logged in successfully"}), 200)
