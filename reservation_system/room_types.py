import os
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
from reservation_system.helpers import format_required_field_error, room_image_location
from werkzeug.utils import secure_filename

bp = Blueprint("room_types", __name__, url_prefix="/room_types", static_folder="static")
table = "room_types"
ALLOWED_EXTENSIONS = {"jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(files):
    if "photo" not in files:
        # check if the post request has the image file part
        flash("No photo part found.")
        return False

    # upload image file
    file = files["photo"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.

    if file.filename == "":
        flash("No selected photo.")
        return False
    if not allowed_file(file.filename):
        flash("Not a valid file type.")
        return False

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(bp.static_folder, room_image_location(), filename))
        return filename


def get_table_fields():
    return [
        "type_name",
        "base_price_per_night",
        "amenities",
        "max_occupants",
    ]


def get_required_fields():
    return [
        "type_name",
        "base_price_per_night",
        "amenities",
        "max_occupants",
    ]


@bp.route("/")
@login_required
def index():
    fields = format_sql_query_columns(get_table_fields() + ["photo", "modified", "modified_by_id", "username"])
    join = f" JOIN users u ON {table}.modified_by_id = u.id"

    room_types = get_all_rows(table, fields, join, order_by="base_price_per_night DESC")

    return render_template("room_types/index.html", room_types=room_types, image_location=room_image_location())


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        filename = upload_file(request.files)
        if filename:
            data = [request.form[f] for f in get_table_fields()] + [filename, g.user["id"]]
            columns = format_sql_query_columns(get_table_fields() + ["photo", "modified_by_id"])
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
                return redirect(url_for("room_types.index"))

    return render_template("room_types/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    room_type = get_row_by_id(
        id,
        table,
        format_sql_query_columns(get_table_fields() + ["photo", "modified_by_id", "username"]),
        f" JOIN users u ON {table}.modified_by_id = u.id",
    )

    if request.method == "POST":
        filename = upload_file(request.files)
        if filename:
            modified = datetime.now()
            data = [request.form[f] for f in get_table_fields()] + [filename, modified, g.user["id"], id]
            columns = format_sql_update_columns(get_table_fields() + ["photo", "modified", "modified_by_id"])

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
                return redirect(url_for("room_types.index"))

    return render_template("room_types/update.html", room_type=room_type, image_location=room_image_location())


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    delete_by_id(id, table)
    return redirect(url_for("room_types.index"))
