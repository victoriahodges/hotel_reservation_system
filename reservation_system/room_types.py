from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("room_types", __name__, url_prefix="/room_types")


def get_fields():
    return [
        "type_name",
        "base_price_per_night",
        "amenities",
        "photo",
        "max_occupants",
    ]


sql_fields = ", ".join(get_fields())
sql_update_fields = " = ?,".join(get_fields())
table = "room_types"


@bp.route("/")
def index():
    db = get_db()
    room_types = db.execute(
        f"SELECT {table}.id, {sql_fields},"
        " modified, modified_by_id, username"
        f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
        " ORDER BY base_price_per_night DESC"
    ).fetchall()
    return render_template("room_types/index.html", room_types=room_types)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
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
            return redirect(url_for("room_types.index"))

    return render_template("room_types/create.html")


def get_room_type(id):
    room_type = (
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

    if room_type is None:
        abort(404, f"Room type id {id} doesn't exist.")

    # if check_guest and post['author_id'] != g.user['id']:
    #     abort(403)

    return room_type


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    room_type = get_room_type(id)

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
                f"UPDATE {table} SET {sql_update_fields} = ?, modified = ?, modified_by_id = ? WHERE id = ?",
                fields,
            )
            db.commit()
            return redirect(url_for("room_types.index"))

    return render_template("room_types/update.html", room_type=room_type)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_room_type(id)
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("room_types.index"))
