"""Repository 抽象接口定义。"""

from __future__ import annotations

from typing import Protocol

from src.models import DailyStats, Game, PlayerRecord, ReviewServer


class ReviewRepository(Protocol):
    """数据访问层接口。SQLite / MySQL 等均实现此 Protocol。"""

    def get_game(self, game_id: str) -> Game | None: ...

    def resolve_game(self, name: str) -> list[Game]:
        """按名称模糊搜索游戏。"""
        ...

    def list_games(self) -> list[Game]: ...

    def get_review_servers(self, game_id: str) -> list[ReviewServer]: ...

    def get_player_records(self, server_id: str, dt: str) -> list[PlayerRecord]: ...

    def get_player_records_page(
        self, server_id: str, dt: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[PlayerRecord], int]:
        """返回 (分页记录, 总数)。"""
        ...

    def get_player_record(self, server_id: str, uid: str, dt: str) -> PlayerRecord | None: ...

    def get_account_creations(self, server_id: str, dt: str) -> list[PlayerRecord]:
        """获取当日新注册的账号。"""
        ...

    def get_formal_crosscheck_uids(self, game_id: str, uids: list[str]) -> list[str]:
        """返回在正式服中存在且有付费的 uid 列表。"""
        ...

    def get_daily_stats(self, server_id: str, start_dt: str, end_dt: str) -> list[DailyStats]: ...

    def save_daily_stats(self, stats: DailyStats) -> None: ...
