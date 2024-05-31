from flask import Blueprint, flash, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("reservation_status", __name__, url_prefix="/reservation_status")


def get_fields():
    return [
        "status",
        "description",
        "bg_color",
    ]


sql_fields = ", ".join(get_fields())
sql_update_fields = " = ?,".join(get_fields())
table = "reservation_status"


@bp.route("/")
def index():
    db = get_db()
    status = db.execute(f"SELECT id, {sql_fields} FROM {table} ORDER BY id").fetchall()
    return render_template("reservation_status/index.html", res_status=status)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        fields = [request.form[f] for f in get_fields()]
        error = None

        # TODO: handle error
        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"INSERT INTO {table} ({sql_fields})" " VALUES (" + ("?, " * len(fields)).rstrip(", ") + ")",
                fields,
            )
            db.commit()
            return redirect(url_for("reservation_status.index"))

    return render_template("reservation_status/create.html")


def get_status(id):
    status = (
        get_db()
        .execute(
            f"SELECT {table}.id, {sql_fields} FROM {table} WHERE {table}.id = ?",
            (id,),
        )
        .fetchone()
    )

    if status is None:
        abort(404, f"Status id {id} doesn't exist.")

    # if check_guest and post['author_id'] != g.user['id']:
    #     abort(403)

    return status


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    status = get_status(id)

    if request.method == "POST":
        fields = [request.form[f] for f in get_fields()] + [id]
        error = None

        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"UPDATE {table} SET {sql_update_fields} = ? WHERE id = ?",
                fields,
            )
            db.commit()
            return redirect(url_for("reservation_status.index"))

    return render_template("reservation_status/update.html", res_status=status)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_status(id)
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("reservation_status.index"))
