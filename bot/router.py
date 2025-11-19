from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Optional

from .config import COMMAND_PREFIX, DEBUG
from .models import MessageEvent


HandlerFunc = Callable[["CommandContext"], Awaitable[None]]


@dataclass
class Command:
    name: str
    description: str
    handler: HandlerFunc


@dataclass
class CommandContext:
    """命令上下文，插件通过它访问事件和回复接口。"""

    event: MessageEvent
    args: List[str]
    reply_func: Callable[[str], Awaitable[None]]
    router: "CommandRouter"

    async def reply(self, text: str) -> None:
        await self.reply_func(text)


@dataclass
class CommandRouter:
    """基于前缀的简单命令路由器，例如 /echo hello"""

    commands: Dict[str, Command] = field(default_factory=dict)

    def command(self, name: str, description: str = "") -> Callable[[HandlerFunc], HandlerFunc]:
        """用作装饰器注册命令。"""

        def decorator(func: HandlerFunc) -> HandlerFunc:
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Command handler must be async function")
            if DEBUG:
                print(f"[router] register command: {name} -> {func.__module__}.{func.__name__}")
            self.commands[name] = Command(name=name, description=description, handler=func)
            return func

        return decorator

    async def handle_message(
        self,
        event: MessageEvent,
        reply_func: Callable[[str], Awaitable[None]],
    ) -> None:
        """根据消息文本解析并分发命令。"""

        text = (event.raw_message or "").strip()
        if not text.startswith(COMMAND_PREFIX):
            return

        # 去掉前缀并拆分
        without_prefix = text[len(COMMAND_PREFIX) :].strip()
        if not without_prefix:
            return

        parts = without_prefix.split()
        cmd_name = parts[0]
        args = parts[1:]

        cmd: Optional[Command] = self.commands.get(cmd_name)
        if cmd is None:
            if DEBUG:
                print(f"[router] unknown command: {cmd_name}")
            return

        ctx = CommandContext(event=event, args=args, reply_func=reply_func, router=self)
        await cmd.handler(ctx)

    def list_commands(self) -> List[Command]:
        return list(self.commands.values())
