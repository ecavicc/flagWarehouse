import os
import threading
import logging

import werkzeug
from flask import Flask

from . import submission_loop


def create_app():
    app = Flask('flagWarehouse', instance_relative_config=False)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    log.disabled = True

    app.config.from_object('config.Config')

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    from . import api
    app.register_blueprint(api.bp)

    if not werkzeug.serving.is_running_from_reloader():
        threading.Thread(target=submission_loop.loop,
                         daemon=True,
                         name='submission_loop',
                         kwargs={'app': app}).start()

    return app
