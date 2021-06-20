import datetime
import random
import sqlite3

usernames = ['ecavicc', 'pippo', 'pluto', 'paperino']
exploits = ['sploit1.py', '1337haxx.py', 'exp1.py', 'pwn.py', 'myexploit.py']
ips = ['10.0.{}.1'.format(i) for i in range(1, 25)]


def rand_time(start: datetime = datetime.datetime.now(), hrs: float = 1) -> datetime:
    stime_ms = (start - datetime.timedelta(hours=hrs)).timestamp()
    etime_ms = start.timestamp()
    rtime_ms = stime_ms + random.random() * (etime_ms - stime_ms)
    return datetime.datetime.fromtimestamp(rtime_ms)


if __name__ == '__main__':
    rows = []
    for i in range(10000):
        status = random.choices(population=['SUBMITTED', 'NOT_SUBMITTED'], weights=(0.1, 1), k=1)[0]
        response = None
        if status == 'SUBMITTED':
            response = random.choice(['SUCCESS', 'ERROR', 'EXPIRED'])
        rows.append(('FLG{{{}}}'.format(str(i).zfill(10)), random.choice(usernames), random.choice(exploits),
                     random.choice(ips), rand_time(hrs=0.001).replace(microsecond=0).isoformat(sep=' '), status, response))

    with sqlite3.connect('../instance/flagWarehouse.sqlite') as con:
        with con as cur:
            # noinspection SqlWithoutWhere
            cur.execute('DELETE FROM flags')
            cur.executemany(
                'INSERT OR IGNORE INTO flags (flag, username, exploit_name, team_ip, time, status, server_response) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)', rows)
