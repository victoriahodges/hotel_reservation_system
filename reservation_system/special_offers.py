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

bp = Blueprint("special_offers", __name__, url_prefix="/special_offers")
table = "special_offers"


def get_table_fields():
    return [
        "title",
        "room_type",
        "price_per_night",
        "start_date",
        "end_date",
        "is_enabled",
    ]


def get_required_fields():
    return [
        "title",
        "room_type",
        "price_per_night",
        "start_date",
        "end_date",
    ]


@bp.route("/")
@login_required
def index():
    fields = format_sql_query_columns(
        get_table_fields() + ["type_name", f"{table}.modified", f"{table}.modified_by_id", "username"]
    )
    join = f"""
    JOIN users u ON {table}.modified_by_id = u.id
    JOIN room_types rt ON {table}.room_type = rt.id
    """

    special_offers = get_all_rows(table, fields, join, order_by="start_date")

    return render_template("special_offers/index.html", special_offers=special_offers)


def get_other_table_rows():
    type_names = get_all_rows("room_types", "id, type_name, base_price_per_night")

    return type_names


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    room_types = get_other_table_rows()

    if request.method == "POST":
        is_enabled = 1 if request.form.get("is_enabled") else 0
        data = [request.form[f] for f in get_table_fields() if f != "is_enabled"] + [is_enabled, g.user["id"]]
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
            return redirect(url_for("special_offers.index"))

    return render_template("special_offers/create.html", room_types=room_types)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    special_offer = get_row_by_id(
        id,
        table,
        format_sql_query_columns(get_table_fields() + ["modified_by_id", "username"]),
        f" JOIN users u ON {table}.modified_by_id = u.id",
    )
    room_types = get_other_table_rows()

    if request.method == "POST":
        modified = datetime.now()
        is_enabled = 1 if request.form.get("is_enabled") else 0
        data = [request.form[f] for f in get_table_fields() if f != "is_enabled"] + [
            is_enabled,
            modified,
            g.user["id"],
            id,
        ]
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
            return redirect(url_for("special_offers.index"))

    return render_template("special_offers/update.html", special_offer=special_offer, room_types=room_types)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    delete_by_id(id, table)
    return redirect(url_for("special_offers.index"))
