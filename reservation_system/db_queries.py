from reservation_system.db import get_db
from werkzeug.exceptions import abort


def format_sql_query_columns(fields):
    return ", ".join(fields)


def format_sql_update_columns(fields):
    return " = ?,".join(fields) + " = ?"


def sql_insert_placeholders(no_of_fields):
    return ("?, " * no_of_fields).rstrip(", ")


def get_all_rows(table, columns, joins=None, order_by=None):
    joins = joins if joins else ""
    order = f"ORDER BY {order_by}" if order_by else ""
    all_rows = get_db().execute(f"SELECT {table}.id, {columns} FROM {table} {joins} {order}").fetchall()

    return all_rows


def get_row_by_id(id, table, columns, joins=None):
    joins = joins if joins else ""
    row = (
        get_db()
        .execute(
            f"SELECT {table}.id, {columns} FROM {table} {joins} WHERE {table}.id = ?",
            (id,),
        )
        .fetchone()
    )

    if row is None:
        abort(404, f"Not found: id {id} in {table} doesn't exist.")

    return row


def get_row_by_where_id(where_column, where_id, table, columns, joins=None):
    joins = joins if joins else ""
    row = (
        get_db()
        .execute(
            f"SELECT {table}.id, {columns} FROM {table} {joins} WHERE {where_column} = ?",
            (where_id,),
        )
        .fetchone()
    )

    if row["id"] is None:
        abort(404, f"Not found: id {where_id} in column {where_column} doesn't exist.")

    return row


def delete_by_id(id, table, param="id", commit=True):
    db = get_db()
    deleted_row = db.execute(f"DELETE FROM {table} WHERE {param} = ?", (id,))
    if deleted_row.rowcount == 0:
        abort(404, f"Not found: id {id} in {table} doesn't exist.")
    if commit:
        db.commit()
