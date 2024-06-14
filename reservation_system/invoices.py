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
    sql_insert_placeholders,
)
from reservation_system.helpers import format_required_field_error

bp = Blueprint("invoices", __name__, url_prefix="/invoices")
table = "invoices"


def get_table_fields():
    return [
        "discount_amount",
        "amount_paid",
    ]


def get_required_fields():
    return []


def get_invoice_summary(reservation_id):
    # returns sum of invoice totals
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            "ir.reservation_id",
            "end_date",
            "SUM(item.total) AS total",
        ]
    )
    join = f"""
    JOIN invoice_items item ON {table}.id = item.invoice_id
    JOIN join_invoices_reservations ir ON {table}.id = ir.invoice_id
    JOIN reservations res ON res.id = ir.reservation_id
    GROUP BY {table}.id
    """

    return get_row_by_id(reservation_id, table, fields, join)


@bp.route("/")
@login_required
def index():
    # returns sum of invoice totals
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            "ir.reservation_id",
            "end_date",
            "g.name",
            "SUM(item.total) AS total",
            f"{table}.created",
            f"{table}.modified",
            f"{table}.modified_by_id",
            "username",
        ]
    )
    join = f"""
    JOIN users u ON {table}.modified_by_id = u.id
    JOIN invoice_items item ON {table}.id = item.invoice_id
    JOIN join_invoices_reservations ir ON {table}.id = ir.invoice_id
    JOIN reservations res ON res.id = ir.reservation_id
    JOIN join_guests_reservations gr ON ir.reservation_id = gr.reservation_id
    JOIN guests g ON gr.guest_id = g.id
    GROUP BY {table}.id
    """

    invoices = get_all_rows(table, fields, join, order_by=f"{table}.created")

    return render_template("invoices/index.html", invoices=invoices)


def get_other_table_rows():
    type_names = get_all_rows("room_types", "id, type_name")

    return type_names


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    room_types = get_other_table_rows()

    if request.method == "POST":
        data = [request.form[f] for f in get_table_fields()] + [g.user["id"]]
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
            return redirect(url_for("rooms.index"))

    return render_template("rooms/create.html", room_types=room_types)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    room = get_row_by_id(
        id,
        table,
        format_sql_query_columns(get_table_fields() + ["modified_by_id", "username"]),
        f" JOIN users u ON {table}.modified_by_id = u.id",
    )
    room_types = get_other_table_rows()

    if request.method == "POST":
        modified = datetime.now()
        data = [request.form[f] for f in get_table_fields()] + [modified, g.user["id"], id]
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
            return redirect(url_for("rooms.index"))

    return render_template("rooms/update.html", room=room, room_types=room_types)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    delete_by_id(id, table)
    return redirect(url_for("rooms.index"))
