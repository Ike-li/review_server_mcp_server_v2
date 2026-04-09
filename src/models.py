"""核心数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Game:
    game_id: str
    name: str
    status: str = "active"  # active / inactive


@dataclass
class ReviewServer:
    server_id: str
    game_id: str
    channel: str  # appstore / googleplay / ...
    version: str
    created_at: str = ""


@dataclass
class PlayerRecord:
    uid: str
    server_id: str
    game_id: str
    dt: str  # 日期 YYYY-MM-DD
    ip: str = ""
    device_id: str = ""
    channel: str = ""
    version: str = ""
    province: str = ""
    country: str = "CN"
    register_time: str = ""
    last_login: str = ""
    total_pay: float = 0.0
    is_formal_server_user: bool = False


@dataclass
class DimensionScore:
    name: str
    weight: float
    raw_score: float  # 0-100
    weighted_score: float  # raw_score * weight
    detail: str = ""


@dataclass
class LeakScore:
    total: float  # 0-100
    level: str  # normal / suspicious / leaked
    dimensions: dict[str, DimensionScore] = field(default_factory=dict)
    summary: str = ""


@dataclass
class DailyStats:
    server_id: str
    dt: str
    player_count: int = 0
    pay_count: int = 0
    new_register_count: int = 0
    unique_ip_count: int = 0
    unique_device_count: int = 0
    leak_score: float = 0.0
    leak_level: str = "normal"
