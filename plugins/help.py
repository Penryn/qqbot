from __future__ import annotations

from bot.router import CommandRouter, CommandContext


def setup(router: CommandRouter) -> None:
    @router.command("help", description="显示所有命令")
    async def help_cmd(ctx: CommandContext) -> None:
        # 简单的帮助信息
        lines = ["可用命令："]
        for cmd in sorted(ctx.router.list_commands(), key=lambda c: c.name):  # type: ignore[attr-defined]
            if cmd.description:
                lines.append(f"/{cmd.name} - {cmd.description}")
            else:
                lines.append(f"/{cmd.name}")

        await ctx.reply("\n".join(lines))

