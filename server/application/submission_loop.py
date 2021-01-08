import time
from datetime import datetime, timedelta
from queue import Queue

import requests
from flask import Flask, current_app
from ordered_set import OrderedSet

from . import db


class OrderedSetQueue(Queue):
    """Unique queue.

    Elements cannot be repeated, so there's no need to traverse it to check.
    LIFO ordered and thread-safe.
    """

    def _init(self, maxsize):
        self.queue = OrderedSet()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()


def loop(app: Flask):
    with app.app_context():
        logger = current_app.logger  # Need to get it before sleep, otherwise it doesn't work. Don't know why.
        # Let's not make it start right away
        time.sleep(5)
        logger.info('starting.')
        database = db.get_db()
        queue = OrderedSetQueue()
        while True:
            s_time = time.time()
            cursor = database.cursor()
            cursor.execute('''
            SELECT flag
            FROM flags
            WHERE time > ? AND status = ?
            ORDER BY time DESC 
            ''', (
                (datetime.now() - timedelta(seconds=current_app.config['FLAG_ALIVE'])).replace(microsecond=0).isoformat(
                    sep=' '), current_app.config['DB_NSUB']))
            for flag in cursor.fetchall():
                queue.put(flag[0])
            i = 0
            queue_length = queue.qsize()
            try:
                while i < min(current_app.config['SUB_LIMIT'], queue_length):
                    flag = queue.get()
                    res = requests.post(current_app.config['SUB_URL'],
                                        data={'team_token': current_app.config['TEAM_TOKEN'], 'flag': flag}).text
                    # executemany() would be better, but it's fine like this.
                    if current_app.config['SUB_ERROR'] in res.lower():
                        cursor.execute('''
                        UPDATE flags
                        SET status = ?, server_response = ?
                        WHERE flag = ?
                        ''', (current_app.config['DB_SUB'], current_app.config['DB_ERR'], flag))
                    elif current_app.config['SUB_ACCEPTED'] in res.lower():
                        cursor.execute('''
                        UPDATE flags
                        SET status = ?, server_response = ?
                        WHERE flag = ?
                        ''', (current_app.config['DB_SUB'], current_app.config['DB_SUCC'], flag))
                    i += 1
                database.commit()
            except requests.exceptions.RequestException:
                logger.error('could not send the flags to the server, retrying...')
            finally:
                duration = time.time() - s_time
                if duration < current_app.config['SUB_INTERVAL']:
                    time.sleep(current_app.config['SUB_INTERVAL'] - duration)
