from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from werkzeug.exceptions import abort

bp = Blueprint("reservations", __name__, url_prefix="/reservations")


def get_fields():
    return [
        "number_of_guests",
        "start_date",
        "end_date",
        "reservation_notes",
        "status_id",
    ]


sql_fields = ", ".join(get_fields())
sql_update_fields = " = ?,".join(get_fields())
table = "reservations"


@bp.route("/")
def index():
    db = get_db()
    reservations = db.execute(
        f"SELECT {table}.id, {sql_fields}, g.name, r.room_number, rs.status, rs.bg_color,"
        f" {table}.modified, {table}.modified_by_id, username"
        f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
        f" JOIN reservation_status rs ON {table}.status_id = rs.id"
        f" JOIN join_guests_reservations gr ON {table}.id = gr.reservation_id"
        f" JOIN guests g ON gr.guest_id = g.id"
        f" JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id"
        f" JOIN rooms r ON rr.room_id = r.id"
        " ORDER BY start_date"
    ).fetchall()
    return render_template("reservations/index.html", reservations=reservations)


def get_rooms():
    type_names = get_db().execute(
        "SELECT r.id, room_number, type_name"
        " FROM rooms r"
        " JOIN room_types rt ON r.room_type = rt.id"
        ).fetchall()

    if type_names is None:
        abort(404, "No Room types found.")

    return type_names


def get_guests():
    guests = get_db().execute("SELECT id, name, address_1 FROM guests").fetchall()

    if guests is None:
        abort(404, "No Guests found.")

    return guests


def get_res_status():
    status = get_db().execute("SELECT * FROM reservation_status").fetchall()

    if status is None:
        abort(404, "No Guests found.")

    return status


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    rooms = get_rooms()
    guests = get_guests()
    res_status = get_res_status()

    if request.method == "POST":
        res_fields = [request.form[f] for f in get_fields()] + [g.user["id"]]
        guest_id = request.form["guest_id"]
        room_id = request.form["room_id"]
        error = None

        # TODO: handle error
        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            # insert row in reservation table
            cur = db.execute(
                f"INSERT INTO {table} ({sql_fields},"
                " modified_by_id)"
                " VALUES (" + ("?, " * len(res_fields)).rstrip(", ") + ")",
                res_fields,
            )

            # get reservation id
            reservation_id = cur.lastrowid

            # insert guest and reservation in joining table
            db.execute(
                "INSERT INTO join_guests_reservations (guest_id, reservation_id) VALUES (?, ?)",
                (guest_id, reservation_id),
            )
            # insert room and reservation in joining table
            db.execute(
                "INSERT INTO join_rooms_reservations (room_id, reservation_id) VALUES (?, ?)",
                (room_id, reservation_id),
            )
            db.commit()
            return redirect(url_for("reservations.index"))

    return render_template("reservations/create.html", guests=guests, res_status=res_status, rooms=rooms)


def get_reservation(id):
    reservation = (
        get_db()
        .execute(
            f"SELECT {table}.id, {sql_fields}, guest_id, room_id,"
            " modified_by_id, username"
            f" FROM {table} JOIN users u ON {table}.modified_by_id = u.id"
            f" JOIN join_guests_reservations gr ON {table}.id = gr.reservation_id"
            f" JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id"
            f" WHERE {table}.id = ?",
            (id,),
        )
        .fetchone()
    )

    if reservation is None:
        abort(404, f"Reservation id {id} doesn't exist.")

    return reservation


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    reservation = get_reservation(id)
    rooms = get_rooms()
    guests = get_guests()
    res_status = get_res_status()

    if request.method == "POST":
        modified = datetime.now()
        fields = [request.form[f] for f in get_fields()] + [modified, g.user["id"], id]
        guest_id = request.form["guest_id"]
        room_id = request.form["room_id"]
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
            db.execute(
                "UPDATE join_guests_reservations SET guest_id = ? WHERE reservation_id = ?",
                (guest_id, id),
            )
            db.execute(
                "UPDATE join_rooms_reservations SET room_id = ? WHERE reservation_id = ?",
                (room_id, id),
            )
            db.commit()
            return redirect(url_for("reservations.index"))

    return render_template("reservations/update.html", reservation=reservation, guests=guests, res_status=res_status, rooms=rooms)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_reservation(id)
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.execute("DELETE FROM join_guests_reservations WHERE reservation_id = ?", (id,))
    db.execute("DELETE FROM join_rooms_reservations WHERE reservation_id = ?", (id,))
    db.commit()
    return redirect(url_for("reservations.index"))
