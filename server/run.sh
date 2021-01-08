#!/usr/bin/env sh

export FLASK_DEBUG=True
export FLASK_APP=application
flask init-db
flask run --host 0.0.0.0