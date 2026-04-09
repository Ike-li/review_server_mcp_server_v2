"""评分引擎测试。"""

from src.engine.dimensions import (
    score_channel_version,
    score_device_distribution,
    score_formal_crosscheck,
    score_geo_distribution,
    score_ip_distribution,
    score_payment,
    score_player_count,
    score_register_time,
)
from src.engine.scoring import calculate_leak_score, classify_level
from src.models import PlayerRecord, ReviewServer
from tests.conftest import DT


def _make_record(**kwargs) -> PlayerRecord:
    defaults = dict(
        uid="u1", server_id="s1", game_id="g1", dt=DT,
        ip="10.0.0.1", device_id="dev-1", channel="appstore", version="1.0.0",
        province="北京", country="CN", register_time="2026-03-01 10:00:00",
        last_login="2026-03-05 14:00:00", total_pay=0.0, is_formal_server_user=False,
    )
    defaults.update(kwargs)
    return PlayerRecord(**defaults)


def _make_server() -> ReviewServer:
    return ReviewServer("s1", "g1", "appstore", "1.0.0")


# ── classify_level ─────────────────────────────────

def test_classify_normal():
    assert classify_level(0) == "normal"
    assert classify_level(30) == "normal"


def test_classify_suspicious():
    assert classify_level(31) == "suspicious"
    assert classify_level(60) == "suspicious"


def test_classify_leaked():
    assert classify_level(61) == "leaked"
    assert classify_level(100) == "leaked"


# ── 各维度（返回 (raw_score, detail) ）─────────────

def test_formal_crosscheck_none():
    records = [_make_record(uid=f"u{i}") for i in range(5)]
    raw, _ = score_formal_crosscheck(records, [])
    assert raw == 0


def test_formal_crosscheck_half():
    records = [_make_record(uid=f"u{i}") for i in range(4)]
    raw, _ = score_formal_crosscheck(records, ["u0", "u1"])
    assert raw == 100  # 50% 交叉即满分


def test_player_count_under_threshold():
    records = [_make_record(uid=f"u{i}") for i in range(10)]
    raw, _ = score_player_count(records, threshold=20)
    assert raw == 0


def test_player_count_over_threshold():
    records = [_make_record(uid=f"u{i}") for i in range(40)]
    raw, _ = score_player_count(records, threshold=20)
    assert raw == 100


def test_ip_few():
    records = [_make_record(uid=f"u{i}", ip="10.0.0.1") for i in range(5)]
    raw, _ = score_ip_distribution(records)
    assert raw == 0


def test_ip_many():
    records = [_make_record(uid=f"u{i}", ip=f"10.0.0.{i}") for i in range(20)]
    raw, _ = score_ip_distribution(records)
    assert raw > 50


def test_payment_none():
    records = [_make_record(uid=f"u{i}") for i in range(5)]
    raw, _ = score_payment(records)
    assert raw == 0


def test_payment_some():
    records = [_make_record(uid=f"u{i}", total_pay=100.0) for i in range(5)]
    raw, _ = score_payment(records)
    assert raw == 100  # 5 个付费即满分


def test_device_few():
    records = [_make_record(uid=f"u{i}", device_id="dev-1") for i in range(5)]
    raw, _ = score_device_distribution(records)
    assert raw == 0


def test_channel_mismatch():
    server = _make_server()
    records = [_make_record(uid=f"u{i}", channel="googleplay") for i in range(4)]
    raw, _ = score_channel_version(records, server)
    assert raw == 100  # 全部不匹配


def test_register_time_today():
    records = [_make_record(uid=f"u{i}", register_time=f"{DT} 09:{i:02d}:00") for i in range(7)]
    raw, _ = score_register_time(records, DT)
    assert raw == 100  # 7 个新注册即满分


def test_geo_single_province():
    records = [_make_record(uid=f"u{i}", province="北京") for i in range(5)]
    raw, _ = score_geo_distribution(records)
    assert raw == 0


def test_geo_multi_province():
    provinces = ["北京", "上海", "广东", "浙江", "四川"]
    records = [_make_record(uid=f"u{i}", province=provinces[i]) for i in range(5)]
    raw, _ = score_geo_distribution(records)
    assert raw == 100


# ── 空数据边界 ─────────────────────────────────────

def test_all_dimensions_empty_records():
    """所有维度评分器应安全处理空列表。"""
    server = _make_server()
    assert score_formal_crosscheck([], [])[0] == 0
    assert score_player_count([], threshold=20)[0] == 0
    assert score_ip_distribution([])[0] == 0
    assert score_payment([])[0] == 0
    assert score_device_distribution([])[0] == 0
    assert score_channel_version([], server)[0] == 0
    assert score_register_time([], DT)[0] == 0
    assert score_geo_distribution([])[0] == 0


# ── 综合评分 ───────────────────────────────────────

def test_calculate_normal(repo):
    records = repo.get_player_records("review-10001-appstore-01", DT)
    server = repo.get_review_servers("10001")[0]
    uids = [r.uid for r in records]
    crosscheck = repo.get_formal_crosscheck_uids("10001", uids)
    score = calculate_leak_score(records, crosscheck, server, DT)
    assert score.level == "normal"
    assert score.total <= 30


def test_calculate_suspicious(repo):
    records = repo.get_player_records("review-10002-appstore-01", DT)
    server = repo.get_review_servers("10002")[0]
    uids = [r.uid for r in records]
    crosscheck = repo.get_formal_crosscheck_uids("10002", uids)
    score = calculate_leak_score(records, crosscheck, server, DT)
    assert score.level == "suspicious"
    assert 30 < score.total <= 60


def test_calculate_leaked(repo):
    records = repo.get_player_records("review-10003-appstore-01", DT)
    server = repo.get_review_servers("10003")[0]
    uids = [r.uid for r in records]
    crosscheck = repo.get_formal_crosscheck_uids("10003", uids)
    score = calculate_leak_score(records, crosscheck, server, DT)
    assert score.level == "leaked"
    assert score.total > 60


# ── 自定义权重 ─────────────────────────────────────

def test_custom_weights_zero_all(repo):
    """全部权重设为 0 时，总分应为 0。"""
    records = repo.get_player_records("review-10003-appstore-01", DT)
    server = repo.get_review_servers("10003")[0]
    uids = [r.uid for r in records]
    crosscheck = repo.get_formal_crosscheck_uids("10003", uids)
    zero_weights = {k: 0.0 for k in [
        "formal_crosscheck", "player_count", "ip_distribution", "payment",
        "device_distribution", "channel_version", "register_time", "geo_distribution",
    ]}
    score = calculate_leak_score(records, crosscheck, server, DT, weights=zero_weights)
    assert score.total == 0
    assert score.level == "normal"
    # 维度权重应反映传入的 0.0
    for d in score.dimensions.values():
        assert d.weight == 0.0
        assert d.weighted_score == 0.0


def test_custom_weights_single_dimension(repo):
    """只给一个维度权重 1.0，其余 0.0 时，总分等于该维度的原始分。"""
    records = repo.get_player_records("review-10003-appstore-01", DT)
    server = repo.get_review_servers("10003")[0]
    uids = [r.uid for r in records]
    crosscheck = repo.get_formal_crosscheck_uids("10003", uids)
    weights = {k: 0.0 for k in [
        "formal_crosscheck", "player_count", "ip_distribution", "payment",
        "device_distribution", "channel_version", "register_time", "geo_distribution",
    ]}
    weights["player_count"] = 1.0
    score = calculate_leak_score(records, crosscheck, server, DT, weights=weights)
    # total 应等于 player_count 的原始分
    assert score.total == score.dimensions["player_count"].raw_score
    assert score.dimensions["player_count"].weight == 1.0
