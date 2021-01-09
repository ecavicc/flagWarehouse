CREATE TABLE IF NOT EXISTS flags
(
    flag            TEXT PRIMARY KEY,
    username        TEXT NOT NULL,
    exploit_name    TEXT NOT NULL,
    team_ip         TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT DEFAULT 'NOT_SUBMITTED',
    server_response TEXT
);

CREATE INDEX IF NOT EXISTS idx_time ON flags (time);