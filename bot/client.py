from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

import websockets
from websockets.client import WebSocketClientProtocol

from . import config
from .models import MessageEvent, OneBotEvent, SendMessageAction


class OneBotClient:
    """
    负责与 LLOneBot (OneBot v11) 建立 WebSocket 连接，接收事件并发送动作。
    """

    def __init__(self, on_message_event: Callable[[MessageEvent], Awaitable[None]]):
        self._on_message_event = on_message_event
        self._ws: Optional[WebSocketClientProtocol] = None
        self._running = False

    @staticmethod
    def _build_ws_url() -> str:
        """在基础 URL 上追加 access_token 查询参数（如果配置了）。"""

        base = config.ONEBOT_WS_URL
        token = config.ACCESS_TOKEN
        if not token:
            return base

        parsed = urlparse(base)
        query = dict(parse_qsl(parsed.query))
        query["access_token"] = token
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))

    async def connect_and_run(self) -> None:
        """连接 LLOneBot 并开始主循环。自动重连。"""

        self._running = True
        while self._running:
            try:
                ws_url = self._build_ws_url()
                print(f"[client] connecting to {ws_url} ...")
                async with websockets.connect(ws_url) as ws:
                    self._ws = ws
                    print("[client] connected to OneBot WebSocket")
                    await self._recv_loop()
            except Exception as e:  # noqa: BLE001
                print(f"[client] connection error: {e!r}, retrying in 5s ...")
                await asyncio.sleep(5)

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        ws = self._ws
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print("[client] invalid JSON:", raw)
                continue

            if "post_type" not in data:
                # 可能是动作响应，忽略
                continue

            try:
                # pydantic v2: 使用 model_validate 代替 parse_obj
                base = OneBotEvent.model_validate(data)
            except Exception as e:  # noqa: BLE001
                print(f"[client] failed to parse OneBotEvent: {e!r}")
                continue

            # 自动更新自己的 self_id
            if base.self_id and not config.BOT_SELF_ID:
                config.BOT_SELF_ID = str(base.self_id)

            if base.post_type == "message":
                try:
                    event = MessageEvent.model_validate(data)
                except Exception as e:  # noqa: BLE001
                    print(f"[client] failed to parse MessageEvent: {e!r}")
                    continue
                await self._on_message_event(event)

    async def send_action(self, action: SendMessageAction) -> None:
        """发送 OneBot v11 动作（例如发送群消息/私聊消息）。"""

        if not self._ws:
            print("[client] cannot send action: not connected")
            return

        payload: Dict[str, Any] = {
            "action": action.action,
            "params": action.params,
            "echo": action.echo or str(uuid.uuid4()),
        }
        raw = json.dumps(payload, ensure_ascii=False)
        await self._ws.send(raw)

    async def send_group_message(self, group_id: int, text: str) -> None:
        await self.send_action(
            SendMessageAction(
                action="send_group_msg",
                params={"group_id": group_id, "message": text},
            )
        )

    async def send_private_message(self, user_id: int, text: str) -> None:
        await self.send_action(
            SendMessageAction(
                action="send_private_msg",
                params={"user_id": user_id, "message": text},
            )
        )
