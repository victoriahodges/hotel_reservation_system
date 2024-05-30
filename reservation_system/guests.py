from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("guests", __name__)


@bp.route("/")
def index():
    db = get_db()
    guests = db.execute(
        "SELECT g.id, name, email, telephone, notes, modified, modified_by_id, username"
        " FROM guests g JOIN users u ON g.modified_by_id = u.id"
        " ORDER BY name"
    ).fetchall()
    return render_template("guests/index.html", guests=guests)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        address_1 = request.form["address_1"]
        address_2 = request.form["address_2"]
        city = request.form["city"]
        county = request.form["county"]
        postcode = request.form["postcode"]
        notes = request.form["notes"]
        error = None

        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO guests (name, email, telephone, address_1,"
                " address_2, city, county, postcode, notes, modified_by_id)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, email, telephone, address_1, address_2, city, county, postcode, notes, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("guests.index"))

    return render_template("guests/create.html")


def get_guest(id):
    guest = (
        get_db()
        .execute(
            "SELECT g.id, name, email, telephone, address_1,"
            " address_2, city, county, postcode, notes,"
            " created, modified_by_id, username"
            " FROM guests g JOIN users u ON g.modified_by_id = u.id"
            " WHERE g.id = ?",
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
        name = request.form["name"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        address_1 = request.form["address_1"]
        address_2 = request.form["address_2"]
        city = request.form["city"]
        county = request.form["county"]
        postcode = request.form["postcode"]
        notes = request.form["notes"]
        modified = datetime.now()
        error = None

        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE guests SET name = ?, email = ?, telephone = ?, address_1 = ?,"
                "address_2 = ?, city = ?, county = ?, postcode = ?, notes = ?,"
                "modified = ?, modified_by_id = ?"
                " WHERE id = ?",
                (
                    name,
                    email,
                    telephone,
                    address_1,
                    address_2,
                    city,
                    county,
                    postcode,
                    notes,
                    modified,
                    g.user["id"],
                    id,
                ),
            )
            db.commit()
            return redirect(url_for("guests.index"))

    return render_template("guests/update.html", guest=guest)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_guest(id)
    db = get_db()
    db.execute("DELETE FROM guests WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("guests.index"))
