import functools

from flask import current_app, Blueprint, flash, g, redirect, render_template, request, session, url_for

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if g.user:
        return redirect(url_for('home.index'))
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if username is None:
            error = 'Please provide a username.'
        elif password != current_app.config['WEB_PASSWORD']:
            current_app.logger.warning(
                f"user {username} ({request.remote_addr}) tried to log in with password {password}.")
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['username'] = username
            current_app.logger.info(f"{username} logged in.")
            return redirect(url_for('home.index'))

        flash(error)

    return render_template('login.html')


@bp.route('/logout')
def logout():
    current_app.logger.info(f"{session['username']} is logging out.")
    session.clear()
    return redirect(url_for('auth.login'))


@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = username


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


def api_auth_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        token = request.headers.get('X-Auth-Token', type=str)
        if token != current_app.config['API_TOKEN']:
            return 'Wrong authorization token', 403
        return view(**kwargs)

    return wrapped_view
