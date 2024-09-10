from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    delete_by_id,
    format_sql_query_columns,
    format_sql_update_columns,
    get_all_rows,
    get_row_by_id,
)
from reservation_system.helpers import format_required_field_error
from werkzeug.security import generate_password_hash

bp = Blueprint("users", __name__, url_prefix="/users")
table = "users"


def get_table_fields():
    return [
        "username",
        "password",
    ]


def get_required_fields():
    return [
        "username",
        "password",
    ]


@bp.route("/")
@login_required
def index():
    fields = format_sql_query_columns(get_table_fields())
    users = get_all_rows(table, fields)
    return render_template("users/index.html", users=users)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        username, password = [request.form[f] for f in get_table_fields()]

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        else:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("users.index"))
            flash(error)

    return render_template("users/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    user = get_row_by_id(id, table, format_sql_query_columns(get_table_fields()))

    if request.method == "POST":
        username, password = [request.form[f] for f in get_table_fields()]
        columns = format_sql_update_columns(get_table_fields())

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        else:
            db = get_db()
            try:
                db.execute(
                    f"UPDATE {table} SET {columns} WHERE id = ?",
                    (username, generate_password_hash(password), id),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("users.index"))
            flash(error)

    return render_template("users/update.html", user=user)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    if id != g.user["id"]:
        delete_by_id(id, table)
    flash(f"Unable to delete {g.user["username"]}. User currently logged in.")
    return redirect(url_for("users.index"))
