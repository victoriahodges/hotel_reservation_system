from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    delete_by_id,
    format_sql_query_columns,
    get_all_rows,
    get_row_by_id,
    get_row_by_where_id,
    sql_insert_placeholders,
)
from reservation_system.helpers import previous_page_url
from reservation_system.invoice_items import calculate_room_invoice_item
from werkzeug.exceptions import NotFound

bp = Blueprint("invoices", __name__, url_prefix="/invoices")
table = "invoices"
parent_page = "invoices.index"


def get_table_fields():
    return [
        f"{table}.reservation_id",
        "discount_amount",
        "amount_paid",
    ]


def get_invoice_items(invoice_id):
    # returns sum of invoice totals
    fields = format_sql_query_columns(
        [
            "item.id as item_id",
            "item.*",
            "reservation_id",
            f"{table}.created",
        ]
    )
    join = f"""
    JOIN invoice_items item ON {table}.id = item.invoice_id
    WHERE item.invoice_id = {invoice_id}
    """
    return get_all_rows(table, fields, join, order_by="item.id")


@bp.route("/")
@login_required
def index():
    # returns sum of invoice totals
    fields = format_sql_query_columns(
        get_table_fields()
        + [
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
    JOIN reservations res ON res.id = {table}.reservation_id
    JOIN join_guests_reservations gr ON {table}.reservation_id = gr.reservation_id
    JOIN guests g ON gr.guest_id = g.id
    GROUP BY {table}.id
    """

    invoices = get_all_rows(table, fields, join, order_by=f"{table}.created")

    return render_template("invoices/index.html", invoices=invoices)


@bp.route("/<int:id>/view")
@login_required
def view(id):
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            f"{table}.id as invoice_id",
            "end_date",
            "g.*",
            "SUM(item.total) AS items_total",
        ]
    )
    join = f"""
    JOIN invoice_items item ON {table}.id = item.invoice_id
    JOIN reservations res ON res.id = {table}.reservation_id
    JOIN join_guests_reservations gr ON {table}.reservation_id = gr.reservation_id
    JOIN guests g ON gr.guest_id = g.id
    """

    invoice = get_row_by_id(id, table, fields, join)
    if invoice["id"]:
        items = get_invoice_items(id)
        balance_due = invoice["items_total"] - invoice["amount_paid"]
        return render_template("invoices/view.html", invoice=invoice, items=items, balance_due=balance_due)

    flash(f"Invoice #{'%05d' % id} does not exist.")
    return redirect(url_for(parent_page))


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        reservation_id = request.form["reservation_id"]
        try:
            # check reservation exists to create invoice
            get_row_by_id(reservation_id, "reservations")
        except NotFound:
            flash(f"Reservation #{'%05d' % int(reservation_id)} does not exist.")
            return redirect(url_for(parent_page))

        try:
            invoice = get_row_by_where_id("invoices.reservation_id", reservation_id, "invoices")
            flash(f"Invoice #{'%05d' % invoice['id']} already exists on another booking.")
        except NotFound:
            # Initialise new invoice with values set to zero for discount and amount_paid
            data = [reservation_id, g.user["id"]]
            columns = format_sql_query_columns(["reservation_id", "modified_by_id"])
            placeholders = sql_insert_placeholders(len(data))

            db = get_db()
            cursor = db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                data,
            )
            # get invoice id
            invoice_id = cursor.lastrowid

            res_columns, res_placeholders, res_data = calculate_room_invoice_item(
                reservation_id, invoice_id, insert=True
            )

            # insert ivoice items for room reservation
            db.execute(
                f"INSERT INTO invoice_items ({res_columns}) VALUES ({res_placeholders})",
                res_data,
            )
            db.commit()

            previous_page = previous_page_url(request.args.get("redirect"))
            if isinstance(previous_page, tuple):
                # return to calendar after creating invoice
                year, month = previous_page
                return redirect(url_for("calendar.calendar", year=year, month=month, reservation_id=reservation_id))

    return redirect(url_for(parent_page))


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    delete_by_id(id, table, commit=False)
    delete_by_id(id, "invoice_items", param="invoice_id")
    return redirect(url_for("invoices.index"))
