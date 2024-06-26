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
from reservation_system.helpers import format_required_field_error, previous_page_url

bp = Blueprint("guests", __name__, url_prefix="/guests")
table = "guests"
parent_page = "guests.index"


def get_table_fields():
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


def get_required_fields():
    return [
        "name",
        "email",
        "telephone",
        "address_1",
        "city",
        "county",
        "postcode",
    ]


@bp.route("/")
@login_required
def index():
    fields = format_sql_query_columns(get_table_fields() + ["created", "modified", "modified_by_id", "username"])
    join = f" JOIN users u ON {table}.modified_by_id = u.id"

    guests = get_all_rows(table, fields, join, order_by="name")

    return render_template("guests/index.html", guests=guests)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
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
            cursor = db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                data,
            )
            guest_id = cursor.lastrowid
            db.commit()

            previous_page = previous_page_url(request.args.get("redirect"))
            if previous_page == "reservations.create":
                # adding new guest when making a new reservation
                return redirect(url_for(previous_page, guest_id=guest_id))
            return redirect(url_for(parent_page))

    return render_template("guests/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    guest = get_row_by_id(
        id,
        table,
        format_sql_query_columns(get_table_fields() + ["created", "modified_by_id", "username"]),
        f" JOIN users u ON {table}.modified_by_id = u.id",
    )

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
            previous_page = previous_page_url(request.args.get("redirect"))
            reservation_id = request.args.get("reservation_id")
            if isinstance(previous_page, tuple):
                # return to calendar after updating guest
                year, month = previous_page
                return redirect(url_for("calendar.calendar", year=year, month=month, reservation_id=reservation_id))
            elif previous_page:
                return redirect(url_for(previous_page, reservation_id=reservation_id))
            return redirect(url_for(parent_page))

    return render_template("guests/update.html", guest=guest)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    # TODO: Warn if there are active bookings connected to guest
    # Delete booking ?
    delete_by_id(id, table)
    return redirect(url_for(parent_page))
