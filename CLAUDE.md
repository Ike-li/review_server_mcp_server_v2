# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

游戏提审服泄漏检测 MCP Server。通过 8 维度加权评分（0-100）自动识别提审包泄漏风险。基于 FastMCP 框架，使用 SQLite 存储。

## Commands

```bash
# 运行全部测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_engine.py -v

# 运行单个测试
pytest tests/test_engine.py::test_classify_normal -v

# 启动 MCP Server
python -m src.server

# 查看 MCP 工具/资源清单
python -m scripts.inspect_mcp
python -m scripts.inspect_mcp --schema    # 含参数 schema
python -m scripts.inspect_mcp --json      # JSON 格式
```

## Architecture

三层架构，依赖方向单向向下：

```
server.py (FastMCP 入口，工具注册)
    ↓
service.py (业务编排层，LeakDetectionService)
    ↓                    ↓
repository/          engine/
  base.py (Protocol)   dimensions.py (8 个纯函数评分器)
  sqlite.py            scoring.py (聚合 + 分级)
```

关键设计决策：
- `ReviewRepository` 是 Protocol（鸭子类型），不是 ABC。新增数据库实现只需满足 Protocol 接口，无需继承。
- `engine/dimensions.py` 中每个评分函数是纯函数，输入 `list[PlayerRecord]` 输出 `(raw_score, detail)`，方便独立测试。
- `Config` 是 frozen dataclass，通过 `Config.from_env()` 从环境变量加载，测试中直接用默认值构造。
- 测试 fixtures 在 `conftest.py` 中通过 `demo_data.seed()` 灌入内存 SQLite，三个场景覆盖 normal/suspicious/leaked。

## Environment Variables

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型 |
| `DB_PATH` | `data/review.db` | SQLite 文件路径 |
| `MCP_HOST` | `127.0.0.1` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |
| `PLAYER_COUNT_THRESHOLD` | `20` | 玩家数量异常阈值 |
| `SEED_DEMO_DATA` | `false` | 启动时灌入样例数据 |

## Scoring System

8 维度权重合计 1.0，定义在 `Config.weights` 和 `engine/scoring.py::_DEFAULT_WEIGHTS`。风险分级：0-30 normal / 31-60 suspicious / 61-100 leaked。

## Code Review Output (AGENTS.md)

代码审查必须在 `codex_review/` 下创建 Markdown 记录，文件名格式 `review_YYYYMMDD_HHMMSS.md`，每次审查一个新文件，不覆盖旧记录。
