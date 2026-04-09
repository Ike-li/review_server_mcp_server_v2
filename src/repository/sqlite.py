"""SQLite 实现 ReviewRepository。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import Config
from src.models import DailyStats, Game, PlayerRecord, ReviewServer

_SCHEMA_SQL = (Path(__file__).parent / "schema.sql").read_text()


class SQLiteRepository:
    """基于 SQLite 的数据访问实现。支持文件和内存两种模式。"""

    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA_SQL)

    def close(self) -> None:
        self._conn.close()

    # ── 游戏 ──────────────────────────────────────────

    def get_game(self, game_id: str) -> Game | None:
        row = self._conn.execute(
            "SELECT game_id, name, status FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        return Game(**row) if row else None

    def resolve_game(self, name: str) -> list[Game]:
        rows = self._conn.execute(
            "SELECT game_id, name, status FROM games WHERE name LIKE ?",
            (f"%{name}%",),
        ).fetchall()
        return [Game(**r) for r in rows]

    def list_games(self) -> list[Game]:
        rows = self._conn.execute("SELECT game_id, name, status FROM games").fetchall()
        return [Game(**r) for r in rows]

    # ── 提审服 ────────────────────────────────────────

    def get_review_servers(self, game_id: str) -> list[ReviewServer]:
        rows = self._conn.execute(
            "SELECT server_id, game_id, channel, version, created_at "
            "FROM review_servers WHERE game_id = ?",
            (game_id,),
        ).fetchall()
        return [ReviewServer(**r) for r in rows]

    # ── 玩家记录 ──────────────────────────────────────

    def get_player_records(self, server_id: str, dt: str) -> list[PlayerRecord]:
        rows = self._conn.execute(
            "SELECT * FROM player_records WHERE server_id = ? AND dt = ?",
            (server_id, dt),
        ).fetchall()
        return [self._to_player_record(r) for r in rows]

    def get_player_record(self, server_id: str, uid: str, dt: str) -> PlayerRecord | None:
        row = self._conn.execute(
            "SELECT * FROM player_records WHERE server_id = ? AND uid = ? AND dt = ?",
            (server_id, uid, dt),
        ).fetchone()
        return self._to_player_record(row) if row else None

    def get_player_records_page(
        self, server_id: str, dt: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[PlayerRecord], int]:
        total = self._conn.execute(
            "SELECT COUNT(*) FROM player_records WHERE server_id = ? AND dt = ?",
            (server_id, dt),
        ).fetchone()[0]
        rows = self._conn.execute(
            "SELECT * FROM player_records WHERE server_id = ? AND dt = ? "
            "ORDER BY uid LIMIT ? OFFSET ?",
            (server_id, dt, limit, offset),
        ).fetchall()
        return [self._to_player_record(r) for r in rows], total

    def get_account_creations(self, server_id: str, dt: str) -> list[PlayerRecord]:
        rows = self._conn.execute(
            "SELECT * FROM player_records "
            "WHERE server_id = ? AND dt = ? AND register_time LIKE ?",
            (server_id, dt, f"{dt}%"),
        ).fetchall()
        return [self._to_player_record(r) for r in rows]

    # ── 正式服交叉 ────────────────────────────────────

    _MAX_SQL_VARS = 32000  # SQLite 限制 32766，留余量

    def get_formal_crosscheck_uids(self, game_id: str, uids: list[str]) -> list[str]:
        if not uids:
            return []
        result: list[str] = []
        batch_size = self._MAX_SQL_VARS - 1  # 减去 game_id 占的 1 个
        for i in range(0, len(uids), batch_size):
            batch = uids[i : i + batch_size]
            placeholders = ",".join("?" for _ in batch)
            rows = self._conn.execute(
                f"SELECT uid FROM formal_server_users "
                f"WHERE game_id = ? AND total_pay > 0 AND uid IN ({placeholders})",
                [game_id, *batch],
            ).fetchall()
            result.extend(r["uid"] for r in rows)
        return result

    # ── 每日统计 ──────────────────────────────────────

    def get_daily_stats(self, server_id: str, start_dt: str, end_dt: str) -> list[DailyStats]:
        rows = self._conn.execute(
            "SELECT * FROM daily_stats "
            "WHERE server_id = ? AND dt >= ? AND dt <= ? ORDER BY dt",
            (server_id, start_dt, end_dt),
        ).fetchall()
        return [DailyStats(**r) for r in rows]

    def save_daily_stats(self, stats: DailyStats) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO daily_stats "
            "(server_id, dt, player_count, pay_count, new_register_count, "
            "unique_ip_count, unique_device_count, leak_score, leak_level) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stats.server_id, stats.dt, stats.player_count, stats.pay_count,
                stats.new_register_count, stats.unique_ip_count, stats.unique_device_count,
                stats.leak_score, stats.leak_level,
            ),
        )
        self._conn.commit()

    # ── 批量写入（demo_data 用）────────────────────────

    def commit(self) -> None:
        self._conn.commit()

    def insert_game(self, game: Game) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO games (game_id, name, status) VALUES (?, ?, ?)",
            (game.game_id, game.name, game.status),
        )

    def insert_review_server(self, server: ReviewServer) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO review_servers (server_id, game_id, channel, version, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (server.server_id, server.game_id, server.channel, server.version, server.created_at),
        )

    def insert_player_record(self, record: PlayerRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO player_records "
            "(uid, server_id, game_id, dt, ip, device_id, channel, version, "
            "province, country, register_time, last_login, total_pay, is_formal_server_user) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.uid, record.server_id, record.game_id, record.dt,
                record.ip, record.device_id, record.channel, record.version,
                record.province, record.country, record.register_time, record.last_login,
                record.total_pay, int(record.is_formal_server_user),
            ),
        )

    def insert_formal_server_user(self, game_id: str, uid: str, total_pay: float = 0.0) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO formal_server_users (game_id, uid, total_pay) VALUES (?, ?, ?)",
            (game_id, uid, total_pay),
        )

    # ── 内部 ──────────────────────────────────────────

    @staticmethod
    def _to_player_record(row: sqlite3.Row) -> PlayerRecord:
        d = dict(row)
        d["is_formal_server_user"] = bool(d["is_formal_server_user"])
        return PlayerRecord(**d)


def create_repository(config: Config) -> SQLiteRepository:
    """工厂函数：根据配置创建 Repository 实例。"""
    if config.db_type != "sqlite":
        raise NotImplementedError(f"暂不支持数据库类型: {config.db_type}")
    db_path = config.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return SQLiteRepository(db_path)
