from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from mcpbridge.client.stdio import run_stdio

if TYPE_CHECKING:
    from mcpbridge.core.context import Context


class Session:
    def __init__(self, ctx: Context):
        self.id = str(uuid.uuid4())
        self.ctx = ctx

    async def start(self) -> None:
        print(f"starting session {self.id}")
        await self._get_tools()

    async def _get_tools(self):
        await run_stdio(self.ctx.mcp_server['stdio']['command'], [str(self.ctx.mcp_server['stdio']['path'])])
