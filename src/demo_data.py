"""样例数据生成：3 个场景（正常 / 可疑 / 泄漏）。"""

from __future__ import annotations

from src.models import DailyStats, Game, PlayerRecord, ReviewServer
from src.repository.sqlite import SQLiteRepository

DT = "2026-03-05"


def seed(repo: SQLiteRepository) -> None:
    """向 repo 中灌入全部样例数据。"""
    _seed_games(repo)
    _seed_servers(repo)
    _seed_normal(repo)
    _seed_suspicious(repo)
    _seed_leaked(repo)
    _seed_daily_stats(repo)
    repo.commit()


# ── 游戏 & 提审服 ────────────────────────────────────

def _seed_games(repo: SQLiteRepository) -> None:
    for g in [
        Game("10001", "星际征途", "active"),
        Game("10002", "仙侠奇缘", "active"),
        Game("10003", "末日狂飙", "active"),
    ]:
        repo.insert_game(g)


def _seed_servers(repo: SQLiteRepository) -> None:
    for s in [
        ReviewServer("review-10001-appstore-01", "10001", "appstore", "1.0.0", "2026-03-01"),
        ReviewServer("review-10002-appstore-01", "10002", "appstore", "2.1.0", "2026-03-01"),
        ReviewServer("review-10003-appstore-01", "10003", "appstore", "3.0.0", "2026-03-01"),
    ]:
        repo.insert_review_server(s)


# ── 场景 1：正常（game 10001）──────────────────────────
# 5 个玩家，全部来自同一 IP/设备/省份，无付费，无交叉

def _seed_normal(repo: SQLiteRepository) -> None:
    server_id = "review-10001-appstore-01"
    for i in range(1, 6):
        repo.insert_player_record(PlayerRecord(
            uid=f"u1_{i:03d}",
            server_id=server_id,
            game_id="10001",
            dt=DT,
            ip="10.0.0.1",
            device_id="device-test-001",
            channel="appstore",
            version="1.0.0",
            province="北京",
            country="CN",
            register_time="2026-03-01 10:00:00",
            last_login=f"{DT} 14:00:00",
        ))


# ── 场景 2：可疑（game 10002）──────────────────────────
# 15 个玩家，4 个正式服交叉，3 个付费，5 个 IP，2 个设备

def _seed_suspicious(repo: SQLiteRepository) -> None:
    server_id = "review-10002-appstore-01"
    ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "192.168.1.1", "172.16.0.1"]
    devices = ["device-a", "device-b"]
    provinces = ["北京", "上海", "广东"]

    for i in range(1, 16):
        pay = 68.0 if i <= 3 else 0.0
        reg_time = f"{DT} 09:{i:02d}:00" if i <= 5 else "2026-03-01 10:00:00"
        repo.insert_player_record(PlayerRecord(
            uid=f"u2_{i:03d}",
            server_id=server_id,
            game_id="10002",
            dt=DT,
            ip=ips[i % len(ips)],
            device_id=devices[i % len(devices)],
            channel="appstore",
            version="2.1.0",
            province=provinces[i % len(provinces)],
            country="CN",
            register_time=reg_time,
            last_login=f"{DT} 15:00:00",
            total_pay=pay,
        ))

    # 正式服交叉用户
    for uid in ["u2_001", "u2_002", "u2_003", "u2_004"]:
        repo.insert_formal_server_user("10002", uid, 100.0)


# ── 场景 3：泄漏（game 10003）──────────────────────────
# 50+ 个玩家，大量交叉，多付费，多 IP/设备/地域，版本不匹配

def _seed_leaked(repo: SQLiteRepository) -> None:
    server_id = "review-10003-appstore-01"
    provinces = ["北京", "上海", "广东", "浙江", "四川", "湖北", "江苏", "福建"]
    countries = ["CN", "CN", "CN", "US", "JP"]

    for i in range(1, 56):
        pay = float(i * 10) if i <= 15 else 0.0
        channel = "googleplay" if i % 4 == 0 else "appstore"
        version = "2.9.0" if i % 5 == 0 else "3.0.0"
        repo.insert_player_record(PlayerRecord(
            uid=f"u3_{i:03d}",
            server_id=server_id,
            game_id="10003",
            dt=DT,
            ip=f"192.168.{i // 10}.{i % 256}",
            device_id=f"device-{i:03d}",
            channel=channel,
            version=version,
            province=provinces[i % len(provinces)],
            country=countries[i % len(countries)],
            register_time=f"{DT} {8 + i % 12}:{i % 60:02d}:00",
            last_login=f"{DT} 20:00:00",
            total_pay=pay,
        ))

    # 大量正式服交叉
    for i in range(1, 26):
        repo.insert_formal_server_user("10003", f"u3_{i:03d}", float(i * 50))


def _seed_daily_stats(repo: SQLiteRepository) -> None:
    # 为泄漏场景补充多日趋势数据
    for day_offset in range(7):
        dt = f"2026-03-{day_offset + 1:02d}"
        player_count = 5 + day_offset * 7  # 逐日增长
        repo.save_daily_stats(DailyStats(
            server_id="review-10003-appstore-01",
            dt=dt,
            player_count=player_count,
            pay_count=day_offset * 2,
            new_register_count=day_offset * 3,
            unique_ip_count=2 + day_offset * 4,
            unique_device_count=2 + day_offset * 5,
            leak_score=min(day_offset * 15.0, 90.0),
            leak_level="normal" if day_offset < 3 else ("suspicious" if day_offset < 5 else "leaked"),
        ))
