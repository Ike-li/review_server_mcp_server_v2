"""评分引擎主逻辑：聚合 8 维度，输出最终 LeakScore。"""

from __future__ import annotations

from src.models import DimensionScore, LeakScore, PlayerRecord, ReviewServer

from .dimensions import (
    score_channel_version,
    score_device_distribution,
    score_formal_crosscheck,
    score_geo_distribution,
    score_ip_distribution,
    score_payment,
    score_player_count,
    score_register_time,
)

_DEFAULT_WEIGHTS: dict[str, float] = {
    "formal_crosscheck": 0.25,
    "player_count": 0.15,
    "ip_distribution": 0.15,
    "payment": 0.15,
    "device_distribution": 0.10,
    "channel_version": 0.10,
    "register_time": 0.05,
    "geo_distribution": 0.05,
}


def calculate_leak_score(
    records: list[PlayerRecord],
    crosscheck_uids: list[str],
    server: ReviewServer,
    dt: str,
    player_count_threshold: int = 20,
    weights: dict[str, float] | None = None,
) -> LeakScore:
    w = weights or _DEFAULT_WEIGHTS

    raw_results: list[tuple[str, float, str]] = [
        ("formal_crosscheck", *score_formal_crosscheck(records, crosscheck_uids)),
        ("player_count", *score_player_count(records, player_count_threshold)),
        ("ip_distribution", *score_ip_distribution(records)),
        ("payment", *score_payment(records)),
        ("device_distribution", *score_device_distribution(records)),
        ("channel_version", *score_channel_version(records, server)),
        ("register_time", *score_register_time(records, dt)),
        ("geo_distribution", *score_geo_distribution(records)),
    ]

    dimensions: dict[str, DimensionScore] = {}
    for name, raw, detail in raw_results:
        weight = w.get(name, 0.0)
        dimensions[name] = DimensionScore(
            name=name,
            weight=weight,
            raw_score=round(raw, 2),
            weighted_score=round(raw * weight, 2),
            detail=detail,
        )

    total = round(sum(d.weighted_score for d in dimensions.values()), 2)
    total = max(0.0, min(100.0, total))
    level = classify_level(total)

    summary = _build_summary(total, level, list(dimensions.values()))

    return LeakScore(
        total=total,
        level=level,
        dimensions=dimensions,
        summary=summary,
    )


def classify_level(score: float) -> str:
    if score <= 30:
        return "normal"
    elif score <= 60:
        return "suspicious"
    else:
        return "leaked"


def _build_summary(total: float, level: str, dims: list[DimensionScore]) -> str:
    level_cn = {"normal": "正常", "suspicious": "可疑", "leaked": "泄漏"}[level]
    lines = [f"综合评分 {total:.1f}/100，风险等级：{level_cn}"]
    top = sorted(dims, key=lambda d: d.raw_score, reverse=True)[:3]
    if top and top[0].raw_score > 0:
        lines.append("主要风险维度：")
        for d in top:
            if d.raw_score > 0:
                lines.append(f"  - {d.name}：{d.detail}")
    return "\n".join(lines)
