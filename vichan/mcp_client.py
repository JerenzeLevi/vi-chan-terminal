"""MCP (Model Context Protocol) client: connect stdio servers such as Playwright and expose their tools.

The official `mcp` SDK is async, so each server runs in its own task on a background event loop.
The task owns the connection for its whole life (anyio requires enter/exit in the same task).
"""
import asyncio
import base64
import os
import re
import shutil
import tempfile
import threading
import time
from pathlib import Path

from .config import CONFIG_DIR
from .tools import Tool


def _g(obj, *names, default=None):
    """First attribute that exists: the mcp SDK renamed camelCase fields to snake_case in 2.x."""
    for n in names:
        v = getattr(obj, n, None)
        if v is not None:
            return v
    return default


def _root(e):
    while getattr(e, "exceptions", None):
        e = e.exceptions[0]
    return e


class MCPManager:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.servers = {}  # name -> {status, error, tools, session, stop}

    # ---- lifecycle
    def start(self, name, cfg):
        self.stop(name)
        info = {"status": "connecting", "error": "", "tools": [], "session": None, "stop": None}
        self.servers[name] = info
        asyncio.run_coroutine_threadsafe(self._serve(name, cfg, info), self.loop)

    def stop(self, name):
        info = self.servers.pop(name, None)
        if info and info["stop"]:
            self.loop.call_soon_threadsafe(info["stop"].set)

    def shutdown(self):
        for name in list(self.servers):
            self.stop(name)
        time.sleep(0.3)  # let subprocesses exit cleanly

    async def _serve(self, name, cfg, info):
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            info.update(status="error", error="the 'mcp' package is missing: pip install mcp")
            return
        info["stop"] = asyncio.Event()
        command = cfg["command"]
        params = StdioServerParameters(
            command=shutil.which(command) or command,
            args=cfg.get("args", []),
            env={**os.environ, **cfg.get("env", {})},
        )
        CONFIG_DIR.mkdir(exist_ok=True)
        log = open(CONFIG_DIR / "mcp.log", "a", encoding="utf-8", errors="replace")
        try:
            async with stdio_client(params, errlog=log) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), 120)
                    listed = await session.list_tools()
                    info["tools"] = [self._wrap(name, session, t) for t in listed.tools]
                    info["session"], info["status"] = session, "ready"
                    await info["stop"].wait()
        except Exception as e:  # noqa: BLE001
            root = _root(e)
            info.update(status="error", error=str(root) or type(root).__name__)
        finally:
            info["session"], info["tools"] = None, []
            if info["status"] != "error":
                info["status"] = "stopped"
            log.close()

    # ---- tools
    def _wrap(self, server, session, t):
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", f"mcp__{server}__{t.name}")[:64]
        ann = getattr(t, "annotations", None)
        readonly = bool(_g(ann, "read_only_hint", "readOnlyHint", default=False))
        schema = dict(_g(t, "input_schema", "inputSchema") or {"type": "object", "properties": {}})
        schema.pop("$schema", None)
        schema.setdefault("type", "object")
        schema.setdefault("properties", {})
        return Tool(
            name=safe,
            description=f"[{server}] {(t.description or t.name)[:900]}",
            parameters=schema,
            fn=lambda **args: self._call(session, t.name, args),
            readonly=readonly,
            approval=not readonly,
        )

    def _call(self, session, tool_name, args):
        fut = asyncio.run_coroutine_threadsafe(session.call_tool(tool_name, args), self.loop)
        res = fut.result(timeout=180)
        parts = []
        for c in res.content:
            kind = getattr(c, "type", "")
            if kind == "text":
                parts.append(c.text)
            elif kind == "image":
                out = Path(tempfile.gettempdir()) / "vichan-mcp"
                out.mkdir(exist_ok=True)
                ext = (_g(c, "mime_type", "mimeType", default="image/png").split("/")[-1] or "png").split("+")[0]
                f = out / f"{int(time.time() * 1000)}.{ext}"
                f.write_bytes(base64.b64decode(c.data))
                parts.append(f"[image saved to {f}]")
        text = "\n".join(parts) or "(no output)"
        return f"error: {text}" if _g(res, "is_error", "isError", default=False) else text

    def tools(self):
        return [t for info in self.servers.values() for t in info["tools"]]
