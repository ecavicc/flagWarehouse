from flask import current_app, Blueprint, request, jsonify

from . import db
from .auth import api_auth_required

bp = Blueprint('api', __name__)


@bp.route('/api/get_config', methods=['GET'])
@api_auth_required
def get_config():
    config_dict = {
        'format': current_app.config['FLAG_FORMAT'],
        'round': current_app.config['ROUND_DURATION'],
        'teams': current_app.config['TEAMS']
    }
    return jsonify(config_dict)


@bp.route('/api/upload_flags', methods=['POST'])
@api_auth_required
def upload_flags():
    data = request.get_json()
    username = data.get('username')
    # current_app.logger.debug(f"{len(data.get('flags'))} flags received from user {username}")
    rows = []
    for item in data.get('flags'):
        rows.append((item.get('flag'), username, item.get('exploit_name'), item.get('team_ip'), item.get('time'),
                     current_app.config['DB_NSUB']))

    database = db.get_db()
    database.executemany('INSERT OR IGNORE INTO flags (flag, username, exploit_name, team_ip, time, status) '
                         'VALUES (?, ?, ?, ?, ?, ?)', rows)
    database.commit()
    return 'Data received', 200
