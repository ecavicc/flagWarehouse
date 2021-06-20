import collections
import functools
import gzip
from datetime import datetime, timedelta
from io import BytesIO

from flask import (
    Blueprint, render_template, request, after_this_request, current_app, jsonify
)

from . import db
from .auth import login_required

bp = Blueprint('home', __name__)


# Slower on localhost, might save your life in any other setting.
# Don't waste your bandwidth, kids.
def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                    response.status_code >= 300 or
                    'Content-Encoding' in response.headers):
                return response
            gzip_buffer = BytesIO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


@bp.route('/', methods=['GET'])
@login_required
@gzipped
def index():
    return render_template('index.html')


@bp.route('/index/chart_data', methods=['GET'])
@login_required
def chart_data():
    try:
        mins = int(request.args['mins'])
    except (ValueError, TypeError):
        return "<h1>Bad request</h1>", 400
    now = datetime.now()
    start = now - timedelta(minutes=mins)
    expiration = now - timedelta(seconds=current_app.config['FLAG_ALIVE'])
    start_s = start.replace(microsecond=0).isoformat(sep=' ')
    expiration_s = expiration.replace(microsecond=0).isoformat(sep=' ')
    cur = db.get_db().cursor()
    if mins != 0:
        cur.execute('''
            SELECT
                SUM(server_response LIKE 'SUCCESS') as accepted,
                SUM(server_response LIKE 'ERROR') as error,
                SUM(status LIKE 'NOT_SUBMITTED' AND time >= ?) AS queued,
                SUM(server_response LIKE 'EXPIRED') AS expired
            FROM flags
            WHERE time >= ?;
            ''', (expiration_s, start_s)
                    )
        doughnut_row = cur.fetchone()
        cur.execute('''
            SELECT
               exploit_name,
               SUM(server_response LIKE 'SUCCESS') AS accepted,
               SUM(server_response LIKE 'ERROR') AS error,
               MIN(time) AS first_occurrence_in_timeframe
            FROM (
                SELECT exploit_name, server_response, time
                FROM flags
                WHERE time >= ?
            )
            GROUP BY exploit_name
            ORDER BY first_occurrence_in_timeframe
            ''', (start_s,))
        barsExploit_rows = cur.fetchall()
        cur.execute('''
            SELECT
               team_ip,
               SUM(server_response LIKE 'SUCCESS') AS accepted,
               SUM(server_response LIKE 'ERROR') AS error
            FROM flags
            WHERE time >= ?
            GROUP BY team_ip
            ORDER BY team_ip
            ''', (start_s,))
        barsTeams_rows = cur.fetchall()
    else:
        cur.execute('''
            SELECT
                SUM(server_response LIKE 'SUCCESS') as accepted,
                SUM(server_response LIKE 'ERROR') as error,
                SUM(status LIKE 'NOT_SUBMITTED' AND time >= ?) AS queued,
                SUM(status LIKE 'NOT_SUBMITTED' AND time < ?) AS expired
            FROM flags
            ''', (expiration_s, expiration_s)
                    )
        doughnut_row = cur.fetchone()
        cur.execute('''
            SELECT
               exploit_name,
               SUM(server_response LIKE 'SUCCESS') AS accepted,
               SUM(server_response LIKE 'ERROR') AS error,
               MIN(time) AS first_occurrence
            FROM flags
            GROUP BY exploit_name
            ORDER BY first_occurrence
            ''')
        barsExploit_rows = cur.fetchall()
        cur.execute('''
            SELECT
               team_ip,
               SUM(server_response LIKE 'SUCCESS') AS accepted,
               SUM(server_response LIKE 'ERROR') AS error,
               MIN(time) AS first_occurrence
            FROM flags
            GROUP BY team_ip
            ORDER BY team_ip
            ''')
        barsTeams_rows = cur.fetchall()

    doughnut_dict = {
        'accepted': doughnut_row[0],
        'error': doughnut_row[1],
        'queued': doughnut_row[2],
        'expired': doughnut_row[3]
    }
    barsExploit_arr = []
    for row in barsExploit_rows:
        barsExploit_arr.append({
            'name': row[0],
            'accepted': row[1],
            'error': row[2]
        })
    barsTeams_arr = []
    for row in barsTeams_rows:
        barsTeams_arr.append({
            'name': row[0],
            'accepted': row[1],
            'error': row[2]
        })

    objects_dict = {'doughnutStatus': doughnut_dict, 'barsExploit': barsExploit_arr, 'barsTeams': barsTeams_arr}
    return jsonify(objects_dict)


@bp.route('/explore', methods=['GET'])
@login_required
@gzipped
def explore():
    cur = db.get_db().cursor()
    cur.execute('SELECT DISTINCT exploit_name FROM flags ORDER BY exploit_name DESC')
    exploits_names = [res[0] for res in cur.fetchall()]
    cur.execute('SELECT DISTINCT username FROM flags ORDER BY username DESC')
    usernames = [res[0] for res in cur.fetchall()]
    cur.execute('SELECT DISTINCT team_ip FROM flags ORDER BY team_ip DESC')
    team_ips = [res[0] for res in cur.fetchall()]

    return render_template('explore.html', exploits_names=exploits_names, usernames=usernames, team_ips=team_ips,
                           statuses=[current_app.config['DB_SUB'], current_app.config['DB_NSUB']],
                           responses=[current_app.config['DB_SUCC'], current_app.config['DB_ERR']],
                           db_nsub=current_app.config['DB_NSUB'])


@bp.route('/explore/get_flags', methods=['GET'])
@login_required
@gzipped
# FIXME: This works, but it's *really* ugly.
#        There must be a better way to do this.
def explore_get_flags():
    statement = 'SELECT * FROM flags'
    where = []
    for k, v in request.args.items():
        if v != '':
            if k == 'since':
                where.append("time >= '" + v + "'")
            elif k == 'until':
                where.append("time <= '" + v + "'")
            else:
                where.append(k + ' = ' + "'" + v + "'")
    if where:
        statement = '{} WHERE {}'.format(statement, ' AND '.join(where))

    cur = db.get_db().cursor()
    # current_app.logger.debug(f"executing query {statement}")
    cur.execute(statement)
    rows = cur.fetchall()
    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['flag'] = row[0]
        d['username'] = row[1]
        d['exploit_name'] = row[2]
        d['team_ip'] = row[3]
        d['time'] = row[4]
        d['status'] = row[5]
        d['response'] = row[6]
        objects_list.append(d)

    # current_app.logger.debug(f"sending {len(rows)} rows.")
    return jsonify(objects_list)
