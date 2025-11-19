from __future__ import annotations

from bot.router import CommandRouter, CommandContext


def setup(router: CommandRouter) -> None:
    @router.command("echo", description="原样回复参数文本")
    async def echo_cmd(ctx: CommandContext) -> None:
        if not ctx.args:
            await ctx.reply("用法：/echo <内容>")
            return
        await ctx.reply(" ".join(ctx.args))

