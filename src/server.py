"""MCP Server 入口：工具注册与启动逻辑。"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastmcp import FastMCP

from src.config import Config
from src.demo_data import seed
from src.models import LeakScore
from src.repository.sqlite import SQLiteRepository, create_repository
from src.service import LeakDetectionService

mcp = FastMCP("提审服泄漏检测")

# ── 初始化 ────────────────────────────────────────────

config = Config.from_env()

if config.db_type == "sqlite":
    db_path = config.db_path
    repo = SQLiteRepository(":memory:") if db_path == ":memory:" else create_repository(config)
else:
    repo = create_repository(config)

if config.seed_demo_data:
    seed(repo)

service = LeakDetectionService(repo, config)


# ── 查询工具（5 个）──────────────────────────────────

@mcp.tool()
def resolve_game(name: str) -> list[dict]:
    """根据名称模糊搜索游戏。返回匹配的游戏列表。"""
    games = service.repo.resolve_game(name)
    return [asdict(g) for g in games]


@mcp.tool()
def query_review_server_status(game_id: str) -> dict:
    """查询指定游戏的提审服状态概览。包括游戏信息和所有提审服列表。"""
    return service.query_status(game_id)


@mcp.tool()
def query_review_server_detail(
    server_id: str, dt: str, page: int = 1, page_size: int = 50
) -> dict:
    """查询提审服用户明细。支持分页。"""
    return service.query_detail(server_id, dt, page, page_size)


@mcp.tool()
def query_formal_crosscheck(game_id: str, server_id: str, dt: str) -> dict:
    """正式服交叉验证：检查提审服玩家中哪些在正式服存在且有付费。"""
    records = service.repo.get_player_records(server_id, dt)
    uids = list({r.uid for r in records})
    crosscheck = service.repo.get_formal_crosscheck_uids(game_id, uids)
    return {
        "total_players": len(uids),
        "crosscheck_count": len(crosscheck),
        "crosscheck_uids": crosscheck,
        "ratio": f"{len(crosscheck)/len(uids):.1%}" if uids else "0%",
    }


@mcp.tool()
def query_account_creations(server_id: str, dt: str) -> dict:
    """查询指定日期的新注册账号统计。"""
    records = service.repo.get_account_creations(server_id, dt)
    return {
        "server_id": server_id,
        "dt": dt,
        "new_accounts": len(records),
        "uids": [r.uid for r in records],
    }


# ── 检测工具（4 个）──────────────────────────────────

@mcp.tool()
def detect_leak(game_id: str, dt: str, server_id: str | None = None) -> dict:
    """全维度泄漏检测。返回 0-100 综合评分和各维度明细。
    如果不指定 server_id，将检测该游戏下所有提审服。"""
    if server_id is not None:
        score = service.detect_leak(game_id, server_id, dt)
        return _score_to_dict(score, server_id)

    servers = service.repo.get_review_servers(game_id)
    results = []
    for s in servers:
        score = service.detect_leak(game_id, s.server_id, dt)
        results.append(_score_to_dict(score, s.server_id))
    return {"game_id": game_id, "dt": dt, "results": results}


@mcp.tool()
def analyze_ip_distribution(server_id: str, dt: str) -> dict:
    """分析提审服的 IP 分布情况。"""
    records = service.repo.get_player_records(server_id, dt)
    ip_map: dict[str, set[str]] = {}
    for r in records:
        if r.ip:
            ip_map.setdefault(r.ip, set()).add(r.uid)
    return {
        "server_id": server_id,
        "dt": dt,
        "unique_ip_count": len(ip_map),
        "player_count": len({r.uid for r in records}),
        "ip_details": {
            ip: {"count": len(uids), "uids": sorted(uids)}
            for ip, uids in ip_map.items()
        },
    }


@mcp.tool()
def analyze_device_distribution(server_id: str, dt: str) -> dict:
    """分析提审服的设备指纹分布。"""
    records = service.repo.get_player_records(server_id, dt)
    device_map: dict[str, set[str]] = {}
    for r in records:
        if r.device_id:
            device_map.setdefault(r.device_id, set()).add(r.uid)
    return {
        "server_id": server_id,
        "dt": dt,
        "unique_device_count": len(device_map),
        "player_count": len({r.uid for r in records}),
        "device_details": {
            dev: {"count": len(uids), "uids": sorted(uids)}
            for dev, uids in device_map.items()
        },
    }


@mcp.tool()
def classify_player(game_id: str, server_id: str, uid: str, dt: str) -> dict:
    """对单个玩家进行风险分类（normal / suspicious / high_risk）。"""
    return service.classify_player(game_id, server_id, uid, dt)


# ── 报告工具（2 个）──────────────────────────────────

@mcp.tool()
def generate_leak_report(game_id: str, server_id: str, dt: str) -> str:
    """生成 Markdown 格式的泄漏检测报告。"""
    return service.generate_report(game_id, server_id, dt)


@mcp.tool()
def get_leak_timeline(server_id: str, start_dt: str, end_dt: str) -> list[dict]:
    """获取多日趋势数据，用于分析泄漏演变。"""
    return service.get_timeline(server_id, start_dt, end_dt)


# ── 辅助工具（1 个）──────────────────────────────────

@mcp.tool()
def get_server_time() -> str:
    """获取服务器当前时间（UTC）。"""
    return datetime.now(timezone.utc).isoformat()


# ── 资源 ─────────────────────────────────────────────

@mcp.resource("games://list")
def list_games() -> list[dict]:
    """获取所有游戏列表。"""
    return [asdict(g) for g in service.repo.list_games()]


@mcp.resource("review-servers://{game_id}")
def get_review_servers(game_id: str) -> list[dict]:
    """获取指定游戏的提审服列表。"""
    return [asdict(s) for s in service.repo.get_review_servers(game_id)]


# ── 内部 ─────────────────────────────────────────────

def _score_to_dict(score: LeakScore, server_id: str) -> dict:
    d = asdict(score)
    d["server_id"] = server_id
    return d


# ── ASGI 入口 ────────────────────────────────────────

mcp_app = mcp.http_app("/mcp")


# ── CLI 启动 ─────────────────────────────────────────

def main():
    mcp.run(transport="streamable-http", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
