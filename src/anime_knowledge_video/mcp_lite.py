"""Dependency-free stdio MCP subset for offline planning tools."""

import json
import sys

from .contracts import GateError
from .episode import create_episode
from .io import ROOT, slug
from .research import load_pack
from .romance.workflow import create_chapter, create_series
from .storyboard import build_storyboard


def schema(required: list[str], properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": required}


def strings(*names: str) -> dict:
    return {name: {"type": "string"} for name in names}


TOOLS = [
    {"name": "create_episode", "description": "Plan a cited 60-second episode; final release is gated.", "inputSchema": schema(["topic"], {**strings("topic", "series", "quality", "research_pack"), "duration_sec": {"type": "integer"}})},
    {"name": "research_episode", "description": "Read a cited local source pack.", "inputSchema": schema(["topic"], strings("topic", "research_pack"))},
    {"name": "write_script", "description": "Return a curated example script.", "inputSchema": schema(["topic"], strings("topic", "research_pack"))},
    {"name": "build_storyboard", "description": "Build a timed shot list.", "inputSchema": schema(["topic"], {**strings("topic", "research_pack"), "duration_sec": {"type": "integer"}})},
    *[{"name": name, "description": "Report pending media provider or QA gate.", "inputSchema": schema(["project_dir"], strings("project_dir"))} for name in ("generate_assets", "generate_voice", "generate_music", "render_episode", "qa_episode")],
    {"name": "create_batch", "description": "Plan at most six curated topics.", "inputSchema": schema(["topics"], {"topics": {"type": "array", "items": {"type": "string"}}, "series": {"type": "string"}})},
    {"name": "create_romance_series", "description": "Initialize an original romance series.", "inputSchema": schema([], strings("series_id"))},
    {"name": "create_romance_chapter", "description": "Plan a 120-second Japanese-dialogue chapter with Chinese captions.", "inputSchema": schema(["series_id", "chapter_number"], {**strings("series_id", "chapter_prompt", "quality"), "chapter_number": {"type": "integer"}, "duration_sec": {"type": "integer"}})},
]


def call_tool(name: str, args: dict) -> object:
    if name == "create_episode":
        return create_episode(**args)
    if name in {"research_episode", "write_script", "build_storyboard"}:
        pack = load_pack(slug(args["topic"]), args.get("research_pack"))
        if name == "research_episode":
            return pack
        if name == "write_script":
            return {"beats": pack["script"], "language": "zh-CN"}
        return build_storyboard(pack["script"], args.get("duration_sec", 60),
                                str(ROOT / "references" / "character_master.png"))
    if name in {"generate_assets", "generate_voice", "generate_music", "render_episode"}:
        return {"status": "blocking_missing", "project_dir": args["project_dir"],
                "reason": "Media provider or render adapter is not configured"}
    if name == "qa_episode":
        return {"status": "pending", "project_dir": args["project_dir"],
                "checks": ["fact", "character", "audio", "subtitle", "ffprobe", "contact sheet"]}
    if name == "create_batch":
        if len(args["topics"]) > 6:
            raise GateError("batch limit is six")
        return [create_episode(topic, series=args.get("series", "cosmos")) for topic in args["topics"]]
    if name == "create_romance_series":
        return create_series(**args)
    if name == "create_romance_chapter":
        return create_chapter(**args)
    raise GateError(f"unknown tool: {name}")


def handle(message: dict) -> dict | None:
    if "id" not in message:
        return None
    request_id = message["id"]
    method = message.get("method")
    try:
        if method == "initialize":
            result = {"protocolVersion": message.get("params", {}).get("protocolVersion", "2025-03-26"),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "anime-knowledge-video", "version": "0.1.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = message.get("params", {})
            value = call_tool(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}
        else:
            return {"jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except (GateError, KeyError, TypeError) as exc:
        return {"jsonrpc": "2.0", "id": request_id, "result":
                {"content": [{"type": "text", "text": str(exc)}], "isError": True}}


def run() -> None:
    for line in sys.stdin:
        try:
            reply = handle(json.loads(line))
            if reply is not None:
                sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    run()
