-- 游戏目录
CREATE TABLE IF NOT EXISTS games (
    game_id   TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    status    TEXT NOT NULL DEFAULT 'active'
);

-- 提审服列表
CREATE TABLE IF NOT EXISTS review_servers (
    server_id   TEXT PRIMARY KEY,
    game_id     TEXT NOT NULL REFERENCES games(game_id),
    channel     TEXT NOT NULL,
    version     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT ''
);

-- 玩家行为记录（核心大表）
CREATE TABLE IF NOT EXISTS player_records (
    uid                   TEXT NOT NULL,
    server_id             TEXT NOT NULL,
    game_id               TEXT NOT NULL,
    dt                    TEXT NOT NULL,
    ip                    TEXT NOT NULL DEFAULT '',
    device_id             TEXT NOT NULL DEFAULT '',
    channel               TEXT NOT NULL DEFAULT '',
    version               TEXT NOT NULL DEFAULT '',
    province              TEXT NOT NULL DEFAULT '',
    country               TEXT NOT NULL DEFAULT 'CN',
    register_time         TEXT NOT NULL DEFAULT '',
    last_login            TEXT NOT NULL DEFAULT '',
    total_pay             REAL NOT NULL DEFAULT 0.0,
    is_formal_server_user INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (uid, server_id, dt)
);

-- 每日统计快照（趋势分析用）
CREATE TABLE IF NOT EXISTS daily_stats (
    server_id          TEXT NOT NULL,
    dt                 TEXT NOT NULL,
    player_count       INTEGER NOT NULL DEFAULT 0,
    pay_count          INTEGER NOT NULL DEFAULT 0,
    new_register_count INTEGER NOT NULL DEFAULT 0,
    unique_ip_count    INTEGER NOT NULL DEFAULT 0,
    unique_device_count INTEGER NOT NULL DEFAULT 0,
    leak_score         REAL NOT NULL DEFAULT 0.0,
    leak_level         TEXT NOT NULL DEFAULT 'normal',
    PRIMARY KEY (server_id, dt)
);

-- 正式服账号交叉表（记录在正式服存在且有付费的 uid）
CREATE TABLE IF NOT EXISTS formal_server_users (
    game_id    TEXT NOT NULL,
    uid        TEXT NOT NULL,
    total_pay  REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (game_id, uid)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_player_records_server_dt ON player_records(server_id, dt);
CREATE INDEX IF NOT EXISTS idx_player_records_game_dt ON player_records(game_id, dt);
CREATE INDEX IF NOT EXISTS idx_review_servers_game ON review_servers(game_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_server ON daily_stats(server_id, dt);
