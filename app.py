import sys

from flask import Flask, abort, render_template, request, jsonify
from flask.helpers import url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import redirect

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://postgres@localhost:5432/todoapp"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app, session_options={"expire_on_commit": False})
migrate = Migrate(app, db)


class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey("todolists.id"), nullable=False)

    def __repr__(self):
        return f"<Todo {self.id}, {self.description}>"

class TodoList(db.Model):
    __tablename__ = "todolists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todos = db.relationship("Todo", backref="list", lazy=True)

@app.route("/todos/create", methods=["POST"])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json()["description"]
        list_id = request.get_json()["list_id"]
        todo = Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body["id"] = todo.id
        body["completed"] = todo.completed
        body["description"] = todo.description
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route("/lists/create", methods=["POST"])
def create_todo_lists():
    error = False
    body = {}
    try:
        new_list = request.get_json()["new_list"]
        todo_list = TodoList(name=new_list, completed=False)
        db.session.add(todo_list)
        db.session.commit()
        body["id"] = todo_list.id
        body["completed"] = todo_list.completed
        body["name"] = todo_list.name
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route("/todos/<todo_id>/set-completed", methods=["POST"])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()["completed"]
        print("completed", completed)
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("index"))


@app.route("/lists/<list_id>/set-completed", methods=["POST"])
def set_completed_todolist(list_id):
    try:
        completed = request.get_json()["completed"]
        print("completed", completed)
        todolist = TodoList.query.get(list_id)
        todolist.completed = completed
        for todo in todolist.todos:
            todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("index"))


@app.route("/todos/<todo_id>/deleted", methods=["DELETE"])
def delete_todo(todo_id):
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({"success": True})


@app.route("/lists/<list_id>/deleted", methods=["DELETE"])
def delete_todo_lists(list_id):
    try:
        list = TodoList.query.get(list_id)
        for todo in list.todos:
            db.session.delete(todo)

        db.session.delete(list)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({"success": True})


@app.route("/lists/<list_id>")
def get_list_todos(list_id):
    return render_template(
        "index.html", 
        lists=TodoList.query.order_by("id").all(),
        active_list=TodoList.query.get(list_id),
        todos=Todo.query.filter_by(list_id=list_id).order_by("id").all(),
    )


@app.route("/")
def index():
    return redirect(url_for("get_list_todos", list_id=1))
