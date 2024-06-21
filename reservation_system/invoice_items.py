from flask import g
from reservation_system.db_queries import (
    format_sql_query_columns,
    format_sql_update_columns,
    get_row_by_id,
    sql_insert_placeholders,
)


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
            ["invoice_id", "item_description", "is_room", "quantity", "amount", "total", "modified_by_id"]
        )
        res_placeholders = sql_insert_placeholders(len(res_data))
        return res_columns, res_placeholders, res_data

    if update:
        res_data = [description, True, no_nights, res["base_price_per_night"], item_total, g.user["id"], invoice_id]
        res_columns = format_sql_update_columns(
            ["item_description", "is_room", "quantity", "amount", "total", "modified_by_id"]
        )
        return res_columns, res_data
