"""业务服务层：编排 Repository 和评分引擎。"""

from __future__ import annotations

from dataclasses import asdict

from src.config import Config
from src.engine.scoring import calculate_leak_score
from src.models import LeakScore
from src.repository.base import ReviewRepository


class LeakDetectionService:
    def __init__(self, repo: ReviewRepository, config: Config | None = None):
        self.repo = repo
        self.config = config or Config()

    # ── 核心检测 ──────────────────────────────────────

    def detect_leak(self, game_id: str, server_id: str, dt: str) -> LeakScore:
        score, _ = self._compute_leak(game_id, server_id, dt)
        return score

    def _compute_leak(
        self, game_id: str, server_id: str, dt: str
    ) -> tuple[LeakScore, list]:
        """返回 (LeakScore, records)，供 detect_leak 和 generate_report 共用。"""
        records = self.repo.get_player_records(server_id, dt)
        servers = self.repo.get_review_servers(game_id)
        server = next((s for s in servers if s.server_id == server_id), None)
        if server is None:
            return LeakScore(total=0, level="normal", summary=f"未找到提审服 {server_id}"), records

        uids = list({r.uid for r in records})
        crosscheck_uids = self.repo.get_formal_crosscheck_uids(game_id, uids)

        score = calculate_leak_score(
            records=records,
            crosscheck_uids=crosscheck_uids,
            server=server,
            dt=dt,
            player_count_threshold=self.config.player_count_threshold,
            weights=self.config.weights,
        )
        return score, records

    # ── 单玩家分类 ────────────────────────────────────

    def classify_player(self, game_id: str, server_id: str, uid: str, dt: str) -> dict:
        record = self.repo.get_player_record(server_id, uid, dt)
        if record is None:
            return {"uid": uid, "classification": "unknown", "detail": "未找到该玩家记录"}

        is_crosscheck = bool(self.repo.get_formal_crosscheck_uids(game_id, [uid]))
        risk_signals: list[str] = []

        if is_crosscheck:
            risk_signals.append("正式服存在且有付费")
        if record.total_pay > 0:
            risk_signals.append(f"提审服付费 {record.total_pay:.2f}")
        if record.register_time.startswith(dt):
            risk_signals.append("当日新注册")

        if len(risk_signals) >= 2:
            classification = "high_risk"
        elif risk_signals:
            classification = "suspicious"
        else:
            classification = "normal"

        return {
            "uid": uid,
            "classification": classification,
            "risk_signals": risk_signals,
            "record": asdict(record),
        }

    # ── 多日趋势 ──────────────────────────────────────

    def get_timeline(self, server_id: str, start_dt: str, end_dt: str) -> list[dict]:
        stats = self.repo.get_daily_stats(server_id, start_dt, end_dt)
        return [asdict(s) for s in stats]

    # ── 报告生成 ──────────────────────────────────────

    def generate_report(self, game_id: str, server_id: str, dt: str) -> str:
        game = self.repo.get_game(game_id)
        game_name = game.name if game else game_id
        score, records = self._compute_leak(game_id, server_id, dt)

        if not score.dimensions:
            return score.summary  # "未找到提审服 ..."

        level_cn = {"normal": "正常", "suspicious": "可疑", "leaked": "泄漏"}.get(score.level, score.level)
        level_emoji = {"normal": "OK", "suspicious": "!!", "leaked": "XX"}.get(score.level, "")

        lines = [
            f"# 提审服泄漏检测报告",
            f"",
            f"- 游戏：{game_name} ({game_id})",
            f"- 提审服：{server_id}",
            f"- 日期：{dt}",
            f"- 综合评分：**{score.total:.1f} / 100** [{level_emoji} {level_cn}]",
            f"",
            f"## 维度明细",
            f"",
            f"| 维度 | 权重 | 原始分 | 加权分 | 说明 |",
            f"|------|------|--------|--------|------|",
        ]
        for d in score.dimensions.values():
            lines.append(
                f"| {d.name} | {d.weight:.0%} | {d.raw_score:.1f} | "
                f"{d.weighted_score:.1f} | {d.detail} |"
            )

        lines += [
            f"",
            f"## 概况",
            f"",
            f"- 独立玩家数：{len({r.uid for r in records})}",
            f"- 独立 IP 数：{len({r.ip for r in records if r.ip})}",
            f"- 独立设备数：{len({r.device_id for r in records if r.device_id})}",
            f"- 付费账号数：{len([r for r in records if r.total_pay > 0])}",
        ]

        return "\n".join(lines)

    # ── 状态概览 ──────────────────────────────────────

    def query_status(self, game_id: str) -> dict:
        game = self.repo.get_game(game_id)
        servers = self.repo.get_review_servers(game_id)
        return {
            "game": asdict(game) if game else None,
            "review_servers": [asdict(s) for s in servers],
            "server_count": len(servers),
        }

    # ── 用户明细 ──────────────────────────────────────

    def query_detail(
        self, server_id: str, dt: str, page: int = 1, page_size: int = 50
    ) -> dict:
        page = max(1, page)
        page_size = max(1, min(page_size, 500))
        offset = (page - 1) * page_size
        page_records, total = self.repo.get_player_records_page(
            server_id, dt, offset=offset, limit=page_size
        )
        return {
            "server_id": server_id,
            "dt": dt,
            "total": total,
            "page": page,
            "page_size": page_size,
            "records": [asdict(r) for r in page_records],
        }
