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


def calculate_leak_score(
    records: list[PlayerRecord],
    crosscheck_uids: list[str],
    server: ReviewServer,
    dt: str,
    player_count_threshold: int = 20,
) -> LeakScore:
    dim_scores: list[DimensionScore] = [
        score_formal_crosscheck(records, crosscheck_uids),
        score_player_count(records, player_count_threshold),
        score_ip_distribution(records),
        score_payment(records),
        score_device_distribution(records),
        score_channel_version(records, server),
        score_register_time(records, dt),
        score_geo_distribution(records),
    ]

    total = round(sum(d.weighted_score for d in dim_scores), 2)
    total = max(0.0, min(100.0, total))
    level = classify_level(total)

    dimensions = {d.name: d for d in dim_scores}

    summary = _build_summary(total, level, dim_scores)

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
    # 列出得分最高的前 3 个维度
    top = sorted(dims, key=lambda d: d.raw_score, reverse=True)[:3]
    if top and top[0].raw_score > 0:
        lines.append("主要风险维度：")
        for d in top:
            if d.raw_score > 0:
                lines.append(f"  - {d.name}：{d.detail}")
    return "\n".join(lines)
