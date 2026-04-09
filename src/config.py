"""配置加载：环境变量 + 默认值。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = str(_PROJECT_ROOT / "data" / "review.db")


@dataclass(frozen=True)
class Config:
    db_type: str = "sqlite"
    db_path: str = _DEFAULT_DB_PATH
    host: str = "127.0.0.1"
    port: int = 8000

    # 评分阈值
    player_count_threshold: int = 20

    # 维度权重（合计 1.0）
    weights: dict[str, float] = field(default_factory=lambda: {
        "formal_crosscheck": 0.25,
        "player_count": 0.15,
        "ip_distribution": 0.15,
        "payment": 0.15,
        "device_distribution": 0.10,
        "channel_version": 0.10,
        "register_time": 0.05,
        "geo_distribution": 0.05,
    })

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            db_path=os.getenv("DB_PATH", _DEFAULT_DB_PATH),
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
            player_count_threshold=int(os.getenv("PLAYER_COUNT_THRESHOLD", "20")),
        )
