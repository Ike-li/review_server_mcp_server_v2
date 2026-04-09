"""8 维度评分器 —— 每个函数是纯函数，输入数据输出分数。"""

from __future__ import annotations

from src.models import DimensionScore, PlayerRecord, ReviewServer


# ── 1. 正式服交叉验证（25%）──────────────────────────

def score_formal_crosscheck(
    records: list[PlayerRecord],
    crosscheck_uids: list[str],
) -> DimensionScore:
    if not records:
        return _make(name="formal_crosscheck", weight=0.25, raw=0, detail="无玩家数据")
    unique_players = len({r.uid for r in records})
    ratio = len(crosscheck_uids) / unique_players if unique_players else 0
    raw = min(ratio * 200, 100)  # 50% 交叉即满分
    detail = f"{len(crosscheck_uids)}/{unique_players} 个账号在正式服存在且有付费 ({ratio:.0%})"
    return _make("formal_crosscheck", 0.25, raw, detail)


# ── 2. 玩家数量异常（15%）────────────────────────────

def score_player_count(
    records: list[PlayerRecord],
    threshold: int = 20,
) -> DimensionScore:
    count = len({r.uid for r in records})
    if count <= threshold:
        raw = 0.0
        detail = f"独立玩家数 {count}，未超过阈值 {threshold}"
    else:
        raw = min((count - threshold) / threshold * 100, 100)
        detail = f"独立玩家数 {count}，超过阈值 {threshold}"
    return _make("player_count", 0.15, raw, detail)


# ── 3. IP 分布分析（15%）─────────────────────────────

def score_ip_distribution(records: list[PlayerRecord]) -> DimensionScore:
    if not records:
        return _make("ip_distribution", 0.15, 0, "无玩家数据")
    unique_ips = {r.ip for r in records if r.ip}
    ip_count = len(unique_ips)
    player_count = len({r.uid for r in records})
    if player_count <= 1:
        return _make("ip_distribution", 0.15, 0, f"仅 {player_count} 个玩家")
    # IP 数远大于预期（提审服通常 1-3 个 IP）
    raw = min((ip_count - 2) / 8 * 100, 100) if ip_count > 2 else 0
    detail = f"{ip_count} 个独立 IP，{player_count} 个玩家"
    return _make("ip_distribution", 0.15, max(raw, 0), detail)


# ── 4. 付费行为分析（15%）────────────────────────────

def score_payment(records: list[PlayerRecord]) -> DimensionScore:
    pay_uids = {r.uid for r in records if r.total_pay > 0}
    count = len(pay_uids)
    if count == 0:
        return _make("payment", 0.15, 0, "无付费账号")
    # 提审服出现付费行为本身就是异常信号
    raw = min(count * 20, 100)  # 5 个付费即满分
    total_amount = sum(r.total_pay for r in records if r.total_pay > 0)
    detail = f"{count} 个付费账号，总金额 {total_amount:.2f}"
    return _make("payment", 0.15, raw, detail)


# ── 5. 设备指纹分析（10%）────────────────────────────

def score_device_distribution(records: list[PlayerRecord]) -> DimensionScore:
    if not records:
        return _make("device_distribution", 0.10, 0, "无玩家数据")
    unique_devices = {r.device_id for r in records if r.device_id}
    count = len(unique_devices)
    # 提审服通常 1-3 台设备
    raw = min((count - 2) / 8 * 100, 100) if count > 2 else 0
    detail = f"{count} 个独立设备"
    return _make("device_distribution", 0.10, max(raw, 0), detail)


# ── 6. 渠道/版本校验（10%）───────────────────────────

def score_channel_version(
    records: list[PlayerRecord],
    server: ReviewServer,
) -> DimensionScore:
    if not records:
        return _make("channel_version", 0.10, 0, "无玩家数据")
    mismatch_uids = {
        r.uid for r in records
        if (r.channel and r.channel != server.channel)
        or (r.version and r.version != server.version)
    }
    total_uids = len({r.uid for r in records})
    count = len(mismatch_uids)
    ratio = count / total_uids if total_uids else 0
    raw = min(ratio * 200, 100)  # 50% 不匹配即满分
    detail = f"{count}/{total_uids} 个玩家的渠道或版本与提审包不匹配 ({ratio:.0%})"
    return _make("channel_version", 0.10, raw, detail)


# ── 7. 注册时间分析（5%）─────────────────────────────

def score_register_time(records: list[PlayerRecord], dt: str) -> DimensionScore:
    new_reg_uids = {r.uid for r in records if r.register_time.startswith(dt)}
    count = len(new_reg_uids)
    # 提审服正常情况下不应有大量当日注册
    raw = min(count * 15, 100)  # 7 个新注册即满分
    detail = f"当日新注册 {count} 个账号"
    return _make("register_time", 0.05, raw, detail)


# ── 8. 地理分布分析（5%）─────────────────────────────

def score_geo_distribution(records: list[PlayerRecord]) -> DimensionScore:
    if not records:
        return _make("geo_distribution", 0.05, 0, "无玩家数据")
    provinces = {r.province for r in records if r.province}
    countries = {r.country for r in records if r.country}
    province_count = len(provinces)
    country_count = len(countries)
    # 跨省/跨国越多越可疑
    raw = min((province_count - 1) / 4 * 100, 100) if province_count > 1 else 0
    if country_count > 1:
        raw = min(raw + 30, 100)
    detail = f"分布于 {province_count} 个省份、{country_count} 个国家"
    return _make("geo_distribution", 0.05, max(raw, 0), detail)


# ── 工具函数 ─────────────────────────────────────────

def _make(name: str, weight: float, raw: float, detail: str) -> DimensionScore:
    return DimensionScore(
        name=name,
        weight=weight,
        raw_score=round(raw, 2),
        weighted_score=round(raw * weight, 2),
        detail=detail,
    )
