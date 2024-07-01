from flask import Blueprint, request, jsonify, make_response
from db import db
from todo.model import Todo

todo = Blueprint('todo', __name__, url_prefix='/todo')

@todo.route('/create', methods=['POST'])
def create_todo():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    new_todo = Todo(title=title, description=description)
    db.session.add(new_todo)
    db.session.commit()
    return make_response(jsonify({"message": "Todo created successfully", "todo": new_todo.serialize()}), 201)