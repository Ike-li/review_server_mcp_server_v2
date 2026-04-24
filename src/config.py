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

    # 飞书机器人 Webhook URL (用于报警)
    feishu_webhook_url: str = ""

    # 飞书 APP 配置 (用于接管消息事件)
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_encrypt_key: str = ""
    feishu_verification_token: str = ""

    # 评分阈值
    player_count_threshold: int = 20

    # 是否灌入样例数据（仅开发/测试用）
    seed_demo_data: bool = False

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
            feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL", ""),
            feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            feishu_encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", ""),
            feishu_verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
            player_count_threshold=int(os.getenv("PLAYER_COUNT_THRESHOLD", "20")),
            seed_demo_data=os.getenv("SEED_DEMO_DATA", "").lower() in ("1", "true", "yes"),
        )
