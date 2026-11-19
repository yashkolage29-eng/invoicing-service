"""Invoice service package."""

import os
from contextlib import closing

from flask import Flask

from . import db
from .api import bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("INVOICE_DB", "invoices.sqlite3")
    if config:
        app.config.update(config)

    with closing(db.connect(app.config["DATABASE"])) as conn:
        db.migrate(conn)

    app.teardown_appcontext(db.close_db)
    app.register_blueprint(bp)
    return app
