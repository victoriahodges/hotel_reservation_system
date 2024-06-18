from datetime import datetime

from flask import Blueprint, redirect, render_template, url_for
from reservation_system.auth import login_required
from reservation_system.db_queries import format_sql_query_columns, get_all_rows
from reservation_system.helpers import room_image_location

bp = Blueprint("calendar", __name__, url_prefix="/calendar")
table = "reservations"


def get_table_fields():
    return [
        "number_of_guests",
        "start_date",
        "end_date",
        "reservation_notes",
        "status_id",
    ]


@bp.route("/")
@login_required
def index():
    return redirect(url_for("calendar.calendar", year=datetime.now().year, month=datetime.now().month))


@bp.route("/<int:year>/<int:month>/")
@login_required
def calendar(year, month):

    # datetime queries and calculations
    # calculate number of days in month
    calendar_start = datetime(year, month, 1)
    month_start = calendar_start.date()
    next_month_start = datetime(year, month + 1, 1) if month + 1 <= 12 else datetime(year + 1, 1, 1)
    no_days_in_month = (next_month_start - calendar_start).days
    calendar_end = datetime(year, month, no_days_in_month)
    month_end = calendar_end.date()

    # generate title for calendar
    title = calendar_start.strftime("%B") + " " + calendar_start.strftime("%Y")

    # dictionary of days and dates
    dates = {d: datetime(year, month, d).date() for d in range(1, no_days_in_month + 1)}

    # previous year link
    prev_year = year - 1 if month == 1 else year

    # previous month link
    prev_month = month - 1 if month > 1 else 12

    # next year link
    next_year = year + 1 if month == 12 else year

    # next month link
    next_month = month + 1 if month < 12 else 1

    # weekends
    weekends = [
        datetime(year, month, d).date()
        for d in range(1, no_days_in_month + 1)
        if datetime(year, month, d).weekday() in (0, 6)
    ]

    # today link
    today_year = datetime.now().year
    today_month = datetime.now().month

    # Database queries
    fields = format_sql_query_columns(
        get_table_fields()
        + [
            "g.id as guest_id",
            "g.*",
            "r.room_number",
            "rt.type_name",
            "rt.base_price_per_night",
            "rt.photo",
            "rt.amenities",
            "rs.status",
            "rs.bg_color",
            "inv.id as invoice_id",
            f"{table}.modified",
            f"{table}.modified_by_id",
            "username",
        ]
    )
    # We only want reservations for this month view, not all time
    where = f""" WHERE end_date > "{calendar_start}" AND start_date < "{calendar_end}" """
    join = f"""
        JOIN users u ON {table}.modified_by_id = u.id
        JOIN reservation_status rs ON {table}.status_id = rs.id
        JOIN join_guests_reservations gr ON {table}.id = gr.reservation_id
        JOIN guests g ON gr.guest_id = g.id
        JOIN join_rooms_reservations rr ON {table}.id = rr.reservation_id
        JOIN rooms r ON rr.room_id = r.id
        JOIN room_types rt ON r.room_type = rt.id
        LEFT JOIN invoices inv ON {table}.id = inv.reservation_id
        {where}
    """

    reservations = get_all_rows(table, fields, join, order_by="start_date")

    room_joins = """
    JOIN users u ON rooms.modified_by_id = u.id
    JOIN room_types rt ON rooms.room_type = rt.id
    """
    rooms = get_all_rows("rooms", "*", room_joins, order_by="room_number")

    # Booking details invoice summaries
    # if invoice exists, get amounts from invoice else derive totals from reservations
    invoices_by_res_id = {}
    for res in reservations:
        invoice = {}
        invoice["invoice_id"] = res["invoice_id"] or None
        invoice["reservation_id"] = res["id"]
        no_nights = (res["end_date"] - res["start_date"]).days
        room_total = invoice["room_total"] = res["base_price_per_night"] * no_nights
        extras = invoice["extras"] = 0  # TODO setup extras
        discount = invoice["discount"] = 0  # TODO setup offers and discounts
        paid_to_date = invoice["paid_to_date"] = 0  # TODO setup payments on account
        invoice["total_due"] = room_total + extras - discount - paid_to_date

        invoices_by_res_id[res["id"]] = invoice

    return render_template(
        "calendar/index.html",
        reservations=reservations,
        rooms=rooms,
        image_location=room_image_location(),
        dates=dates,
        title=title,
        year=year,
        month=month,
        date_now=datetime.now().date(),
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        today_month=today_month,
        today_year=today_year,
        month_start=month_start,
        month_end=month_end,
        weekends=weekends,
        invoices=invoices_by_res_id,
    )
