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

bp = Blueprint("payments", __name__, url_prefix="/payments")
table = "payments"


def get_table_fields():
    return [
        "invoice_id",
        "amount",
    ]


def get_required_fields():
    return [
        "amount",
    ]


@bp.route("/")
@login_required
def index():
    # returns sum of invoice totals
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            "end_date",
            "g.name",
            "invoices.reservation_id",
            f"{table}.created",
            f"{table}.modified",
            f"{table}.modified_by_id",
            "username",
        ]
    )
    join = f"""
    JOIN users u ON {table}.modified_by_id = u.id
    JOIN invoices ON {table}.invoice_id = invoices.id
    JOIN reservations res ON res.id = invoices.reservation_id
    JOIN join_guests_reservations gr ON res.id = gr.reservation_id
    JOIN guests g ON gr.guest_id = g.id
    """

    payments = get_all_rows(table, fields, join, order_by=f"{table}.created")

    return render_template("payments/index.html", payments=payments)


def get_paid_to_date(invoice_id):
    rows = get_all_rows(table, "SUM(amount) as total", f"WHERE invoice_id = {invoice_id} GROUP BY invoice_id")
    return rows[0]["total"]


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    reservation_id = request.args.get("reservation_id")
    if request.method == "POST":
        invoice_id = request.form["invoice_id"]

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
            # update invoice amount_paid
            db.execute(
                "UPDATE invoices SET amount_paid = ? WHERE id = ?",
                (get_paid_to_date(invoice_id), invoice_id)
            )
            db.commit()
            previous_page = request.args.get("redirect")
            return redirect(
                url_for("invoices.view", id=invoice_id, reservation_id=reservation_id, redirect=previous_page)
            )

    return render_template("payments/create.html", reservation_id=reservation_id)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    reservation_id = request.args.get("reservation_id")
    items = get_row_by_id(id, table, format_sql_query_columns(get_table_fields()))

    if request.method == "POST":
        modified = datetime.now()
        invoice_id = request.form["invoice_id"]

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
            # update invoice amount_paid
            db.execute(
                "UPDATE invoices SET amount_paid = ? WHERE id = ?",
                (get_paid_to_date(invoice_id), invoice_id)
            )
            db.commit()
            previous_page = request.args.get("redirect")
            return redirect(
                url_for("invoices.view", id=invoice_id, reservation_id=reservation_id, redirect=previous_page)
            )

    return render_template("payments/update.html", items=items, reservation_id=reservation_id)
