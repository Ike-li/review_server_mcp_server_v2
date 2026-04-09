"""查看当前 MCP Server 注册的 tools / resources / prompts。"""

from __future__ import annotations

import argparse
import asyncio
import json


async def _inspect(args):
    from src.server import mcp

    tools = await mcp.list_tools()
    resources = await mcp.list_resources()
    templates = await mcp.list_resource_templates()

    if args.json:
        data = {
            "tools": {
                t.name: {
                    "description": t.description or "",
                    **({"inputSchema": t.inputSchema} if args.schema and hasattr(t, 'inputSchema') else {}),
                }
                for t in tools
            },
            "resources": {
                str(r.uri): {"description": r.description or ""}
                for r in resources
            },
            "resource_templates": {
                str(getattr(t, 'uri_template', '')): {"description": t.description or ""}
                for t in templates
            },
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print(f"\n{'='*60}")
    print(f"  提审服泄漏检测 MCP Server")
    print(f"{'='*60}")

    print(f"\n## Tools ({len(tools)})\n")
    for t in tools:
        desc = (t.description or "").split("\n")[0]
        print(f"  - {t.name}: {desc}")
        if args.schema and hasattr(t, 'inputSchema'):
            schema = t.inputSchema
            if isinstance(schema, dict) and "properties" in schema:
                for pname, pinfo in schema["properties"].items():
                    ptype = pinfo.get("type", "any")
                    required = pname in schema.get("required", [])
                    req_mark = "*" if required else " "
                    print(f"      {req_mark} {pname}: {ptype}")

    print(f"\n## Resources ({len(resources)})\n")
    for r in resources:
        print(f"  - {r.uri}: {r.description or ''}")

    if templates:
        print(f"\n## Resource Templates ({len(templates)})\n")
        for t in templates:
            uri = getattr(t, 'uri_template', getattr(t, 'uriTemplate', str(t)))
            print(f"  - {uri}: {t.description or ''}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Inspect MCP Server capabilities")
    parser.add_argument("--schema", action="store_true", help="显示参数 schema")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()
    asyncio.run(_inspect(args))


if __name__ == "__main__":
    main()
