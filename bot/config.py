from __future__ import annotations

import os

from dotenv import load_dotenv

"""
基础配置。

优先从环境变量读取，便于通过 .env 或部署平台注入：
- ONEBOT_WS_URL
- ONEBOT_ACCESS_TOKEN
"""

# 自动加载项目根目录的 .env
load_dotenv()

# LLOneBot 提供的 OneBot v11 WebSocket 地址
# 根据官方示例配置，默认 ws 正向连接只需要端口，不需要额外路径
ONEBOT_WS_URL: str = os.getenv("ONEBOT_WS_URL", "ws://127.0.0.1:3001")

# 如果 LLOneBot 的 ob11.ws 配置了 token，则填写与其相同的值；
# 未开启则留空。Python 端会自动在 WebSocket URL 上追加 ?access_token=TOKEN。
ACCESS_TOKEN: str | None = os.getenv("ONEBOT_ACCESS_TOKEN") or None

# 机器人自己的 QQ 号（可选）
# 如果留空，运行过程中会自动从事件中获取并更新
BOT_SELF_ID: str | None = None

# 命令前缀，例如：/echo
COMMAND_PREFIX: str = "/"

# 是否输出 debug 日志
DEBUG: bool = True
