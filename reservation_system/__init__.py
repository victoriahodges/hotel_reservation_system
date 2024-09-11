import os
from datetime import datetime

from flask import Flask, render_template
from reservation_system.auth import login_required
from reservation_system.db_queries import count_rows, format_sql_query_columns, get_all_rows

from . import (
    auth,
    calendar,
    db,
    guests,
    invoice_items,
    invoices,
    payments,
    reservation_status,
    reservations,
    room_types,
    rooms,
    special_offers,
    users,
)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "reservations.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # load the homepage
    @app.route("/")
    @login_required
    def index():
        fields = format_sql_query_columns(
            [
                "start_date",
                "end_date",
                "total_room_base_price",
                "special_offer_discount",
                "reservation_notes",
                "status_id",
                "g.name",
                "r.room_number",
                "rs.status",
                "rs.bg_color",
                "reservations.modified",
                "reservations.modified_by_id",
                "username",
            ]
        )
        join = """
            JOIN users u ON reservations.modified_by_id = u.id
            JOIN reservation_status rs ON reservations.status_id = rs.id
            JOIN join_guests_reservations gr ON reservations.id = gr.reservation_id
            JOIN guests g ON gr.guest_id = g.id
            JOIN join_rooms_reservations rr ON reservations.id = rr.reservation_id
            JOIN rooms r ON rr.room_id = r.id
            JOIN room_types rt ON r.room_type = rt.id
        """
        reservations = get_all_rows("reservations", fields, join, order_by="reservations.id DESC LIMIT 5")

        today = datetime.now().strftime("%Y-%m-%d")
        arrivals = count_rows("reservations", f"WHERE start_date = '{today}'")
        departures = count_rows("reservations", f"WHERE end_date = '{today}'")
        stays = count_rows("reservations", f"WHERE start_date < '{today}' AND end_date > '{today}'")
        bookings_today = count_rows("reservations", f"WHERE substr(created, 1, 10) = '{today}'")

        return render_template(
            "overview/index.html",
            reservations=reservations,
            arrivals=arrivals,
            departures=departures,
            stays=stays,
            bookings_today=bookings_today,
        )

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.add_url_rule("/", endpoint="users.index")
    app.register_blueprint(calendar.bp)
    app.add_url_rule("/", endpoint="calendar.index")
    app.register_blueprint(guests.bp)
    app.add_url_rule("/", endpoint="guests.index")
    app.register_blueprint(room_types.bp)
    app.add_url_rule("/", endpoint="room_types.index")
    app.register_blueprint(rooms.bp)
    app.add_url_rule("/", endpoint="rooms.index")
    app.register_blueprint(reservations.bp)
    app.add_url_rule("/", endpoint="reservations.index")
    app.register_blueprint(reservation_status.bp)
    app.add_url_rule("/", endpoint="reservation_status.index")
    app.register_blueprint(special_offers.bp)
    app.add_url_rule("/", endpoint="special_offers.index")
    app.register_blueprint(invoices.bp)
    app.add_url_rule("/", endpoint="invoices.index")
    app.register_blueprint(invoice_items.bp)
    app.add_url_rule("/", endpoint="invoice_items.create")
    app.register_blueprint(payments.bp)
    app.add_url_rule("/", endpoint="payments.index")

    return app
