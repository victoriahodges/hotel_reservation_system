from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("guests", __name__, url_prefix="/guests")


def get_fields():
    return [
        "name",
        "email",
        "telephone",
        "address_1",
        "address_2",
        "city",
        "county",
        "postcode",
        "guest_notes",
    ]


sql_fields = ", ".join(get_fields())
sql_update_fields = " = ?,".join(get_fields())
table = "guests"


@bp.route("/")
def index():
    db = get_db()
    guests = db.execute(
        f"SELECT {table}.id, {sql_fields},"
        " modified, modified_by_id, username"
        f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
        " ORDER BY name"
    ).fetchall()
    return render_template("guests/index.html", guests=guests)


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
            return redirect(url_for("guests.index"))

    return render_template("guests/create.html")


# TODO: refactor into row query function and import
def get_guest(id):
    guest = (
        get_db()
        .execute(
            f"SELECT {table}.id, {sql_fields},"
            " created, modified_by_id, username"
            f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
            f" WHERE {table}.id = ?",
            (id,),
        )
        .fetchone()
    )

    if guest is None:
        abort(404, f"Guest id {id} doesn't exist.")

    # if check_guest and post['author_id'] != g.user['id']:
    #     abort(403)

    return guest


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    guest = get_guest(id)

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
            return redirect(url_for("guests.index"))

    return render_template("guests/update.html", guest=guest)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_guest(id)
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("guests.index"))
