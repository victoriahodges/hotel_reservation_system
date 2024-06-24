from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    delete_by_id,
    format_sql_query_columns,
    format_sql_update_columns,
    get_row_by_id,
    sql_insert_placeholders,
)
from reservation_system.helpers import format_required_field_error

bp = Blueprint("invoice_items", __name__, url_prefix="/invoice_items")
table = "invoice_items"


def get_table_fields():
    return [
        "invoice_id",
        "item_description",
        "quantity",
        "price",
        "total",
    ]


def get_required_fields():
    return [
        "item_description",
        "quantity",
        "price",
    ]


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    reservation_id = request.args.get("reservation_id")
    if request.method == "POST":
        invoice_id = request.form["invoice_id"]
        total = float(request.form["price"]) * int(request.form["quantity"])

        data = [request.form[f] for f in get_table_fields() if f != "total"] + [total, g.user["id"]]
        columns = format_sql_query_columns(get_table_fields() + ["modified_by_id"])
        placeholders = sql_insert_placeholders(len(data))

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        else:
            db = get_db()
            db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                data,
            )
            db.commit()
            previous_page = request.args.get("redirect")
            return redirect(
                url_for("invoices.view", id=invoice_id, reservation_id=reservation_id, redirect=previous_page)
            )

    return render_template("invoice_items/create.html", reservation_id=reservation_id)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    reservation_id = request.args.get("reservation_id")
    items = get_row_by_id(id, table, format_sql_query_columns(get_table_fields()))

    if request.method == "POST":
        modified = datetime.now()
        invoice_id = request.form["invoice_id"]
        total = float(request.form["price"]) * int(request.form["quantity"])
        data = [request.form[f] for f in get_table_fields() if f != "total"] + [total, modified, g.user["id"], id]
        columns = format_sql_update_columns(get_table_fields() + ["modified", "modified_by_id"])

        # handle required field errors
        error_fields = []
        for required in get_required_fields():
            if not request.form[required]:
                error_fields.append(required)

        if error_fields:
            flash(format_required_field_error(error_fields))
        else:
            db = get_db()
            db.execute(
                f"UPDATE {table} SET {columns} WHERE id = ?",
                data,
            )
            db.commit()
            previous_page = request.args.get("redirect")
            return redirect(
                url_for("invoices.view", id=invoice_id, reservation_id=reservation_id, redirect=previous_page)
            )

    return render_template("invoice_items/update.html", items=items, reservation_id=reservation_id)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    reservation_id = request.form["reservation_id"]
    invoice_id = request.form["invoice_id"]
    delete_by_id(id, table)
    previous_page = request.args.get("redirect")
    return redirect(url_for("invoices.view", id=invoice_id, reservation_id=reservation_id, redirect=previous_page))


def get_reservation(id):
    reservation = get_row_by_id(
        id,
        "reservations",
        format_sql_query_columns(
            [
                "start_date",
                "end_date",
                "room_number",
                "type_name",
                "base_price_per_night",
            ]
        ),
        """
          JOIN join_rooms_reservations rr ON reservations.id = rr.reservation_id
          JOIN rooms on rr.room_id = rooms.id
          JOIN room_types rt ON rooms.room_type = rt.id
        """,
    )
    return reservation


def calculate_room_invoice_item(reservation_id, invoice_id, insert=None, update=None):
    res = get_reservation(reservation_id)
    # automatically updates the room item after changes made to booking
    description = f"Room {res['room_number']}: {res['type_name']}"
    no_nights = (res["end_date"] - res["start_date"]).days
    item_total = res["base_price_per_night"] * no_nights

    if insert:
        res_data = [invoice_id, description, True, no_nights, res["base_price_per_night"], item_total, g.user["id"]]
        res_columns = format_sql_query_columns(
            ["invoice_id", "item_description", "is_room", "quantity", "price", "total", "modified_by_id"]
        )
        res_placeholders = sql_insert_placeholders(len(res_data))
        return res_columns, res_placeholders, res_data

    if update:
        res_data = [description, True, no_nights, res["base_price_per_night"], item_total, g.user["id"], invoice_id]
        res_columns = format_sql_update_columns(
            ["item_description", "is_room", "quantity", "price", "total", "modified_by_id"]
        )
        return res_columns, res_data
