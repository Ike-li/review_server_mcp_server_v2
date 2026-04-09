"""8 维度评分器 -- 每个函数是纯函数，输入数据输出原始分（0-100）。"""

from __future__ import annotations

from src.models import PlayerRecord, ReviewServer


# ── 1. 正式服交叉验证 ────────────────────────────────

def score_formal_crosscheck(
    records: list[PlayerRecord],
    crosscheck_uids: list[str],
) -> tuple[float, str]:
    """返回 (raw_score, detail)。"""
    if not records:
        return 0, "无玩家数据"
    unique_players = len({r.uid for r in records})
    ratio = len(crosscheck_uids) / unique_players if unique_players else 0
    raw = min(ratio * 200, 100)  # 50% 交叉即满分
    detail = f"{len(crosscheck_uids)}/{unique_players} 个账号在正式服存在且有付费 ({ratio:.0%})"
    return raw, detail


# ── 2. 玩家数量异常 ──────────────────────────────────

def score_player_count(
    records: list[PlayerRecord],
    threshold: int = 20,
) -> tuple[float, str]:
    count = len({r.uid for r in records})
    if count <= threshold:
        return 0, f"独立玩家数 {count}，未超过阈值 {threshold}"
    raw = min((count - threshold) / threshold * 100, 100)
    return raw, f"独立玩家数 {count}，超过阈值 {threshold}"


# ── 3. IP 分布分析 ───────────────────────────────────

def score_ip_distribution(records: list[PlayerRecord]) -> tuple[float, str]:
    if not records:
        return 0, "无玩家数据"
    unique_ips = {r.ip for r in records if r.ip}
    ip_count = len(unique_ips)
    player_count = len({r.uid for r in records})
    if player_count <= 1:
        return 0, f"仅 {player_count} 个玩家"
    raw = max(min((ip_count - 2) / 8 * 100, 100), 0) if ip_count > 2 else 0
    return raw, f"{ip_count} 个独立 IP，{player_count} 个玩家"


# ── 4. 付费行为分析 ──────────────────────────────────

def score_payment(records: list[PlayerRecord]) -> tuple[float, str]:
    pay_uids = {r.uid for r in records if r.total_pay > 0}
    count = len(pay_uids)
    if count == 0:
        return 0, "无付费账号"
    raw = min(count * 20, 100)  # 5 个付费即满分
    total_amount = sum(r.total_pay for r in records if r.total_pay > 0)
    return raw, f"{count} 个付费账号，总金额 {total_amount:.2f}"


# ── 5. 设备指纹分析 ──────────────────────────────────

def score_device_distribution(records: list[PlayerRecord]) -> tuple[float, str]:
    if not records:
        return 0, "无玩家数据"
    unique_devices = {r.device_id for r in records if r.device_id}
    count = len(unique_devices)
    raw = max(min((count - 2) / 8 * 100, 100), 0) if count > 2 else 0
    return raw, f"{count} 个独立设备"


# ── 6. 渠道/版本校验 ─────────────────────────────────

def score_channel_version(
    records: list[PlayerRecord],
    server: ReviewServer,
) -> tuple[float, str]:
    if not records:
        return 0, "无玩家数据"
    mismatch_uids = {
        r.uid for r in records
        if (r.channel and r.channel != server.channel)
        or (r.version and r.version != server.version)
    }
    total_uids = len({r.uid for r in records})
    count = len(mismatch_uids)
    ratio = count / total_uids if total_uids else 0
    raw = min(ratio * 200, 100)  # 50% 不匹配即满分
    return raw, f"{count}/{total_uids} 个玩家的渠道或版本与提审包不匹配 ({ratio:.0%})"


# ── 7. 注册时间分析 ──────────────────────────────────

def score_register_time(records: list[PlayerRecord], dt: str) -> tuple[float, str]:
    new_reg_uids = {r.uid for r in records if r.register_time.startswith(dt)}
    count = len(new_reg_uids)
    raw = min(count * 15, 100)  # 7 个新注册即满分
    return raw, f"当日新注册 {count} 个账号"


# ── 8. 地理分布分析 ──────────────────────────────────

def score_geo_distribution(records: list[PlayerRecord]) -> tuple[float, str]:
    if not records:
        return 0, "无玩家数据"
    provinces = {r.province for r in records if r.province}
    countries = {r.country for r in records if r.country}
    province_count = len(provinces)
    country_count = len(countries)
    raw = max(min((province_count - 1) / 4 * 100, 100), 0) if province_count > 1 else 0
    if country_count > 1:
        raw = min(raw + 30, 100)
    return raw, f"分布于 {province_count} 个省份、{country_count} 个国家"
