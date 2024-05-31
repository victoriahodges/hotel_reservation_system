from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("rooms", __name__, url_prefix="/rooms")


def get_fields():
    return [
        "room_number",
        "room_type",
    ]


sql_fields = ", ".join(get_fields())
sql_update_fields = " = ?,".join(get_fields())
table = "rooms"


@bp.route("/")
def index():
    db = get_db()
    rooms = db.execute(
        f"SELECT {table}.id, {sql_fields},"
        f" {table}.modified, {table}.modified_by_id, username, type_name"
        f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
        f" JOIN room_types rt ON {table}.room_type = rt.id"
        " ORDER BY room_number"
    ).fetchall()
    return render_template("rooms/index.html", rooms=rooms)


def get_room_type_names():
    type_names = (
        get_db()
        .execute(
            "SELECT id, type_name FROM room_types"
        )
        .fetchall()
    )

    if type_names is None:
        abort(404, "No Room types found.")

    return type_names


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    room_types = get_room_type_names()
    
    if request.method == "POST":
        fields = [request.form[f] for f in get_fields()] + [g.user["id"]]
        error = None

        # TODO: handle error
        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"INSERT INTO {table} ({sql_fields},"
                " modified_by_id)"
                " VALUES (" + ("?, " * len(fields)).rstrip(", ") + ")",
                fields,
            )
            db.commit()
            return redirect(url_for("rooms.index"))

    return render_template("rooms/create.html", room_types=room_types)


def get_room(id):
    room = (
        get_db()
        .execute(
            f"SELECT {table}.id, {sql_fields},"
            " modified_by_id, username"
            f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
            f" WHERE {table}.id = ?",
            (id,),
        )
        .fetchone()
    )

    if room is None:
        abort(404, f"Room id {id} doesn't exist.")

    return room


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    room = get_room(id)
    room_types = get_room_type_names()

    if request.method == "POST":
        modified = datetime.now()
        fields = [request.form[f] for f in get_fields()] + [modified, g.user["id"], id]
        error = None

        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"UPDATE {table} SET {sql_update_fields} = ?," " modified = ?, modified_by_id = ?" " WHERE id = ?",
                fields,
            )
            db.commit()
            return redirect(url_for("rooms.index"))

    return render_template("rooms/update.html", room=room, room_types=room_types)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_room(id)
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("rooms.index"))
