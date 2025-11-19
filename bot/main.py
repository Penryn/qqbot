from __future__ import annotations

import asyncio

from .client import OneBotClient
from .config import DEBUG
from .models import MessageEvent
from .router import CommandRouter

# 插件导入（可以在这里新增插件）
from plugins import echo, help as help_plugin  # noqa: F401


router = CommandRouter()


def load_plugins() -> None:
    """
    插件约定：
    - 每个插件模块提供一个 `setup(router: CommandRouter)` 函数
    - 在这里统一调用
    """

    echo.setup(router)
    help_plugin.setup(router)


async def handle_message_event(client: OneBotClient, event: MessageEvent) -> None:
    """接收到 OneBot 消息事件时的处理逻辑。"""

    if DEBUG:
        print(
            f"[main] message event: type={event.message_type} "
            f"group_id={event.group_id} user_id={event.user_id} text={event.raw_message!r}"
        )

    async def reply(text: str) -> None:
        if event.message_type == "group" and event.group_id:
            await client.send_group_message(event.group_id, text)
        elif event.message_type == "private" and event.user_id:
            await client.send_private_message(event.user_id, text)
        else:
            # 其他类型先忽略
            if DEBUG:
                print("[main] cannot reply: unknown message_type")

    await router.handle_message(event, reply)


async def main() -> None:
    load_plugins()

    client: OneBotClient | None = None

    async def on_event(ev: MessageEvent) -> None:
        assert client is not None
        await handle_message_event(client, ev)

    client = OneBotClient(on_message_event=on_event)

    await client.connect_and_run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bye")
