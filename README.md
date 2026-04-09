# 提审服泄漏检测 MCP Server

基于 [Model Context Protocol](https://modelcontextprotocol.io/) 的游戏提审服泄漏检测系统。通过 8 维度综合评分（0-100 分）自动识别提审包泄漏风险。

## 快速开始

### 安装

```bash
pip install fastmcp pytest
```

### 启动 MCP Server

```bash
python -m src.server
```

服务监听 `http://127.0.0.1:8000/mcp`。ASGI 入口：`src.server:mcp_app`。

环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型 |
| `DB_PATH` | `data/review.db` | SQLite 文件路径 |
| `MCP_HOST` | `127.0.0.1` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |
| `PLAYER_COUNT_THRESHOLD` | `20` | 玩家数量异常阈值 |

### 测试与调试

```bash
pytest tests/ -v                          # 运行测试（39 个用例）
python -m scripts.inspect_mcp             # 查看 MCP 工具/资源清单
python -m scripts.inspect_mcp --schema    # 含参数 schema
python -m scripts.inspect_mcp --json      # JSON 格式输出
```

## MCP 工具一览

共 12 个工具 + 2 个资源。

| 类别 | 工具 | 功能 |
|------|------|------|
| **查询** | `resolve_game` | 游戏名称模糊搜索 |
| | `query_review_server_status` | 提审服状态概览 |
| | `query_review_server_detail` | 用户明细查询（分页） |
| | `query_formal_crosscheck` | 正式服交叉验证 |
| | `query_account_creations` | 账号注册统计 |
| **检测** | `detect_leak` | 全维度泄漏检测（核心） |
| | `analyze_ip_distribution` | IP 分布分析 |
| | `analyze_device_distribution` | 设备指纹分析 |
| | `classify_player` | 单个玩家风险分类 |
| **报告** | `generate_leak_report` | 生成 Markdown 报告 |
| | `get_leak_timeline` | 多日趋势分析 |
| **辅助** | `get_server_time` | 获取服务器时间 |

### 使用示例

```
"检测游戏 10003 在 2026-03-05 的提审服是否泄漏"
→ detect_leak(game_id="10003", dt="2026-03-05")
```

## 检测引擎

### 8 维度评分

| 维度 | 权重 | 说明 |
|------|------|------|
| 正式服交叉验证 | 25% | 提审服账号在正式服存在且付费 |
| 玩家数量异常 | 15% | 独立玩家数超过正常阈值 |
| IP 分析 | 15% | 独立 IP 数量 |
| 付费行为分析 | 15% | 提审服付费账号数量 |
| 设备指纹分析 | 10% | 独立设备数量 |
| 渠道/版本校验 | 10% | 非提审包连接检测 |
| 注册时间分析 | 5% | 当日新注册账号数量 |
| 地理分布分析 | 5% | 跨省份/国家分布 |

### 风险分级

| 评分区间 | 等级 | 建议 |
|----------|------|------|
| 0 - 30 | Normal（正常） | 无明显泄漏信号 |
| 31 - 60 | Suspicious（可疑） | 密切监控 |
| 61 - 100 | Leaked（泄漏） | 立即下架 |

## 架构

```
src/
├── config.py           # 配置（环境变量 + 默认值）
├── models.py           # 数据模型（dataclass）
├── server.py           # FastMCP 入口，工具注册
├── service.py          # 业务服务层
├── demo_data.py        # 样例数据（3 场景）
├── repository/
│   ├── base.py         # Repository Protocol（抽象接口）
│   ├── sqlite.py       # SQLite 实现
│   └── schema.sql      # 建表 SQL
└── engine/
    ├── dimensions.py   # 8 个维度评分器（纯函数）
    └── scoring.py      # 评分聚合
scripts/
    └── inspect_mcp.py  # MCP 能力查看
tests/                  # 39 个测试用例
```

**数据层可切换**：通过 `ReviewRepository` Protocol 抽象数据访问，SQLite 为默认实现。未来可添加 MySQL/PostgreSQL 实现而不改动业务逻辑。

## 技术栈

- **FastMCP** - MCP Server 框架
- **SQLite** - 数据存储（内置 schema + 样例数据）
- **pytest** - 测试框架

## License

MIT
