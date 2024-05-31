import os

from flask import Flask, render_template

from . import auth, db, guests, reservation_status, reservations, room_types, rooms


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
    def index():
        return render_template("homepage/index.html")

    db.init_app(app)

    app.register_blueprint(auth.bp)
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

    return app
