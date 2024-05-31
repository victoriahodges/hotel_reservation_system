from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    format_sql_query_columns,
    format_sql_update_columns,
    get_all_rows,
    get_row_by_id,
    sql_insert_placeholders,
)

bp = Blueprint("guests", __name__, url_prefix="/guests")
table = "guests"


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


@bp.route("/")
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

        error = None

        # TODO: handle error
        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                data,
            )
            db.commit()
            return redirect(url_for("guests.index"))

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
        error = None

        # if not name:
        #     error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                f"UPDATE {table} SET {columns} WHERE id = ?",
                data,
            )
            db.commit()
            return redirect(url_for("guests.index"))

    return render_template("guests/update.html", guest=guest)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("guests.index"))
