"""
插件包。

每个插件模块应提供：

    def setup(router: CommandRouter) -> None: ...

由 `bot.main.load_plugins` 调用。
"""

