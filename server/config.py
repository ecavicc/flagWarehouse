class Config(object):
    WEB_PASSWORD = 'password'
    API_TOKEN = 'token'

    YOUR_TEAM = '10.0.2.1'
    TEAM_TOKEN = 'ThIsIsAtEaMtOkEn'
    TEAMS = ['10.0.{}.1'.format(i) for i in range(1, 30)]
    TEAMS.remove(YOUR_TEAM)

    ROUND_DURATION = 60
    FLAG_ALIVE = 5 * ROUND_DURATION
    FLAG_FORMAT = r'FLAG\{[A-Za-z0-9]{25}\}'

    SUB_LIMIT = 50
    SUB_INTERVAL = 1
    SUB_URL = 'http://localhost:8000'
    SUB_ACCEPTED = 'accepted'
    SUB_ERROR = 'error'

    DB_NSUB = 'NOT_SUBMITTED'
    DB_SUB = 'SUBMITTED'
    DB_SUCC = 'SUCCESS'
    DB_ERR = 'ERROR'

    SECRET_KEY = 'dev'

    DATABASE = 'instance/flagWarehouse.sqlite'
