from flask import Blueprint, flash, redirect, render_template, request, url_for
from reservation_system.auth import login_required
from reservation_system.db import get_db
from reservation_system.db_queries import (
    format_sql_query_columns,
    format_sql_update_columns,
    get_all_rows,
    get_row_by_id,
    sql_insert_placeholders,
)
from reservation_system.helpers import format_required_field_error

bp = Blueprint("reservation_status", __name__, url_prefix="/reservation_status")
table = "reservation_status"


def get_table_fields():
    return [
        "status",
        "description",
        "bg_color",
    ]


def get_required_fields():
    return [
        "status",
    ]


@bp.route("/")
def index():
    fields = format_sql_query_columns(get_table_fields())

    status = get_all_rows(table, fields, order_by="id")

    return render_template("reservation_status/index.html", res_status=status)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        data = [request.form[f] for f in get_table_fields()]
        columns = format_sql_query_columns(get_table_fields())
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
            return redirect(url_for("reservation_status.index"))

    return render_template("reservation_status/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    status = get_row_by_id(id, table, format_sql_query_columns(get_table_fields()))

    if request.method == "POST":
        data = [request.form[f] for f in get_table_fields()] + [id]
        columns = format_sql_update_columns(get_table_fields())

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
            return redirect(url_for("reservation_status.index"))

    return render_template("reservation_status/update.html", res_status=status)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("reservation_status.index"))
