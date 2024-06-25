from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    delete_by_id,
    format_sql_query_columns,
    format_sql_update_columns,
    get_all_rows,
    get_row_by_id,
    get_row_by_where_id,
    sql_insert_placeholders,
)
from reservation_system.helpers import format_required_field_error, previous_page_url
from reservation_system.invoice_items import calculate_room_invoice_item
from werkzeug.exceptions import NotFound

bp = Blueprint("reservations", __name__, url_prefix="/reservations")
table = "reservations"
parent_page = "reservations.index"


def get_table_fields():
    return [
        "number_of_guests",
        "start_date",
        "end_date",
        "reservation_notes",
        "status_id",
    ]


def get_required_fields():
    return [
        "number_of_guests",
        "start_date",
        "end_date",
        "status_id",
        "room_id",
        "guest_id",
    ]


# RESERVATION RULES
reservation_collision_message = "BOOKING COLLISION: Please choose alternative dates."
end_date_before_start_date_message = "DATE ERROR: Check-out date cannot be before or same as check-in date."
dates_in_the_past_message = "DATE ERROR: Check-in or check-out dates cannot be in the past."


def find_existing_reservation_collisions(id=None):
    # Purpose: Prevent double bookings

    not_include_this_res_id = ""
    if id:
        # to enable updating a booking dates and does not collide with itself
        not_include_this_res_id = f"AND {table}.id IS NOT {id} "

    reservations = get_all_rows(
        table,
        f"{table}.id, start_date, end_date, r.id",
        f"""
            JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id
            JOIN rooms r ON rr.room_id = r.id
            WHERE {request.form["room_id"]} = r.id {not_include_this_res_id}AND (
            -- outside booking
            ("{request.form['start_date']}" <= start_date AND "{request.form['end_date']}" >= end_date)
            -- inside booking
            OR ("{request.form['start_date']}" >= start_date AND "{request.form['end_date']}" <= end_date)
            -- overlap start_date
            OR ("{request.form['start_date']}" <= start_date AND "{request.form['end_date']}" > start_date)
            -- overlap end_date
            OR ("{request.form['start_date']}" < end_date AND "{request.form['end_date']}" >= end_date)
            )
            """,
    )
    return reservations


def end_date_before_start_date():
    # Purpose: Prevent choosing check-out before check-in
    if request.form["end_date"] <= request.form["start_date"]:
        return True
    return False


def reservation_dates_in_the_past():
    # Purpose: Prevent choosing check-in or check-out dates in the past
    if (
        datetime.strptime(request.form["start_date"], "%Y-%m-%d") < datetime.now()
        and datetime.strptime(request.form["end_date"], "%Y-%m-%d") <= datetime.now()
    ):
        return True
    return False


@bp.route("/")
@login_required
def index():
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            "g.name",
            "r.room_number",
            "rt.base_price_per_night",
            "rs.status",
            "rs.bg_color",
            f"{table}.modified",
            f"{table}.modified_by_id",
            "username",
        ]
    )
    join = f"""
        JOIN users u ON {table}.modified_by_id = u.id
        JOIN reservation_status rs ON {table}.status_id = rs.id
        JOIN join_guests_reservations gr ON {table}.id = gr.reservation_id
        JOIN guests g ON gr.guest_id = g.id
        JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id
        JOIN rooms r ON rr.room_id = r.id
        JOIN room_types rt ON r.room_type = rt.id
    """

    reservations = get_all_rows(table, fields, join, order_by="start_date")

    return render_template("reservations/index.html", reservations=reservations)


def get_other_table_rows():
    rooms = get_all_rows(
        "rooms",
        "room_number, type_name, max_occupants",
        " JOIN room_types rt ON rooms.room_type = rt.id",
        order_by="room_number",
    )
    guests = get_all_rows("guests", "id, name, address_1", order_by="name")
    res_statuses = get_all_rows("reservation_status", "*")
    return rooms, guests, res_statuses


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    rooms, guests, res_statuses = get_other_table_rows()

    max_occupants = max([r["max_occupants"] for r in rooms])

    if request.method == "POST":
        data = [request.form[f] for f in get_table_fields()] + [g.user["id"]]
        guest_id = request.form["guest_id"]
        room_id = request.form["room_id"]
        columns = format_sql_query_columns(get_table_fields() + ["modified_by_id"])
        placeholders = sql_insert_placeholders(len(data))

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        elif end_date_before_start_date():
            flash(end_date_before_start_date_message)
        elif find_existing_reservation_collisions():
            flash(reservation_collision_message)
        elif reservation_dates_in_the_past():
            flash(dates_in_the_past_message)
        else:
            db = get_db()
            # insert row in reservation table
            cursor = db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                data,
            )

            # get reservation id
            reservation_id = cursor.lastrowid

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

            # new bookings should return to the calendar page for the dates selected
            year = datetime.strptime(request.form["start_date"], "%Y-%m-%d").year
            month = datetime.strptime(request.form["start_date"], "%Y-%m-%d").month
            return redirect(url_for("calendar.calendar", year=year, month=month, reservation_id=reservation_id))

    return render_template(
        "reservations/create.html",
        guests=guests,
        res_statuses=res_statuses,
        rooms=rooms,
        number_of_guests=max_occupants,
    )


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    reservation = get_row_by_id(
        id,
        table,
        format_sql_query_columns(
            get_table_fields()
            + [
                "guest_id",
                "room_id",
            ]
        ),
        f"""
          JOIN users u ON {table}.modified_by_id = u.id
          JOIN join_guests_reservations gr ON {table}.id = gr.reservation_id
          JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id
        """,
    )
    rooms, guests, res_statuses = get_other_table_rows()

    max_occupants = max([r["max_occupants"] for r in rooms])

    if request.method == "POST":
        modified = datetime.now()
        data = [request.form[f] for f in get_table_fields()] + [modified, g.user["id"], id]
        guest_id = request.form["guest_id"]
        room_id = request.form["room_id"]
        columns = format_sql_update_columns(get_table_fields() + ["modified", "modified_by_id"])

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        elif end_date_before_start_date():
            flash(end_date_before_start_date_message)
        elif find_existing_reservation_collisions(id):
            flash(reservation_collision_message)
        # elif reservation_dates_in_the_past():
        #     flash(dates_in_the_past_message)
        else:
            db = get_db()
            db.execute(
                f"UPDATE {table} SET {columns} WHERE id = ?",
                data,
            )
            # update guest in joining table
            db.execute(
                "UPDATE join_guests_reservations SET guest_id = ? WHERE reservation_id = ?",
                (guest_id, id),
            )
            # update room in joining table
            db.execute(
                "UPDATE join_rooms_reservations SET room_id = ? WHERE reservation_id = ?",
                (room_id, id),
            )
            # update_room_invoice()
            try:
                invoice = get_row_by_where_id("invoices.reservation_id", id, "invoices")
                res_columns, res_data = calculate_room_invoice_item(id, invoice["id"])
                db.execute(
                    f"UPDATE invoice_items SET {res_columns} WHERE invoice_id = ? AND is_room = TRUE",
                    res_data,
                )
            except NotFound:
                pass
            db.commit()

            # existing bookings should return to the calendar page for the dates selected
            year = datetime.strptime(request.form["start_date"], "%Y-%m-%d").year
            month = datetime.strptime(request.form["start_date"], "%Y-%m-%d").month
            return redirect(url_for("calendar.calendar", year=year, month=month, reservation_id=id))

    return render_template(
        "reservations/update.html",
        reservation=reservation,
        guests=guests,
        res_statuses=res_statuses,
        rooms=rooms,
        number_of_guests=max_occupants,
    )


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    delete_by_id(id, table, commit=False)
    delete_by_id(id, "join_guests_reservations", param="reservation_id", commit=False)
    delete_by_id(id, "join_rooms_reservations", param="reservation_id")
    previous_page = previous_page_url(request.form["redirect"])
    if isinstance(previous_page, tuple):
        # return to calendar after deleting reservation
        year, month = previous_page
        return redirect(url_for("calendar.calendar", year=year, month=month))
    elif previous_page:
        return redirect(url_for(previous_page))
    return redirect(url_for(parent_page))
