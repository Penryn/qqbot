# QQ Bot (Python) via LLOneBot / OneBot v11

本项目是一个使用 Python 通过 **LLOneBot**（实现 OneBot v11 协议）的 QQ 机器人脚手架，特点：

- 基于 `asyncio` 和 WebSocket
- 简单插件机制：按命令前缀路由到不同插件
- 方便扩展：在 `plugins/` 目录里新增文件即可增加功能

> 说明：这里的代码在容器中未实际运行，请在你本机安装依赖并测试。

## 目录结构

- `bot/`
  - `config.py`：配置（LLOneBot 地址、访问令牌、机器人 QQ 号等）
  - `client.py`：与 LLOneBot 建立 WebSocket 连接，收发 OneBot v11 事件/动作
  - `router.py`：简单的命令路由器
  - `models.py`：部分 OneBot v11 事件/动作的数据结构（只定义了用到的部分）
  - `main.py`：入口，初始化并运行机器人
- `plugins/`
  - `__init__.py`
  - `echo.py`：示例插件（`/echo xxx`）
  - `help.py`：示例插件（`/help` 列出命令）

## 运行前准备

### 1. 用 Docker 启动 LLOneBot（推荐）

前提：本机已安装并启动 Docker（Docker Desktop 等）。

在本项目根目录执行：

```bash
docker compose -f docker-compose.llonebot.yml up -d
```

首次启动会自动拉取镜像并创建两个容器：

- `llob-pmhq`：QQ 客户端及辅助程序
- `llob-core`：LLOneBot 本体

默认已映射端口：

- `3080`：WebUI（配置界面）
- `3001`：OneBot v11 WebSocket 正向连接
- `3000`：OneBot v11 HTTP 接口

启动成功后：

1. 打开浏览器访问 `http://localhost:3080`，使用 `docker-compose.llonebot.yml` 中的 `WEBUI_TOKEN` 登录（默认 `change_me`，建议你自己改）。
2. 在 WebUI 中登录 QQ（按页面提示扫码等）。
3. 在配置里找到 OneBot 11 (`ob11`) 部分，确认：
   - 有一条 `type: "ws"` 的连接
   - `enable: true`
   - `port: 3001`
   - （可选）`token` 不为空时，记住这个值，后面要配置到 Python 端。

LLOneBot 的配置文件一般在容器内的 `data/config_<qq号>.json`，通过 WebUI 修改后会自动重载。

### 2. 安装 Python 依赖

在本项目目录下执行（需 Python 3.9+）：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 下为 .venv\\Scripts\\activate
pip install -U pip
pip install websockets pydantic
```

依赖说明：

- `websockets`：异步 WebSocket 客户端
- `pydantic`：用于把 JSON 映射为 Python 对象（可选，但更方便）

### 3. 配置机器人

修改 `bot/config.py` 中的内容：

- `ONEBOT_WS_URL`：保持默认 `ws://127.0.0.1:3001` 即可（对应上面 Docker 暴露的 ws 端口）
- `ACCESS_TOKEN`：如果在 LLOneBot 的 `ob11.connect` 中给 ws 连接配置了 `token`，这里填同样的字符串，否则留空
- `BOT_SELF_ID`：可以先留空，机器人连上后会自动从事件里记住自己的 QQ 号

### 4. 运行机器人

在项目根目录执行：

```bash
source .venv/bin/activate  # 如果尚未激活虚拟环境
python -m bot.main
```

看到终端输出 “Connected to OneBot …” 即表示连上了。

此时在任意群里对机器人发送：

- `/echo 你好` → 机器人会原样回复 “你好”
- `/help` → 会列出可用命令列表

## 编写插件

在 `plugins/` 目录中新建一个文件，例如 `ping.py`：

```python
from bot.router import CommandRouter, CommandContext


def setup(router: CommandRouter):
    @router.command("ping", description="测试连通性")
    async def ping(ctx: CommandContext):
        await ctx.reply("pong")
```

随后在 `bot/main.py` 中引入该插件（见文件内注释）。

你也可以根据自己的需要扩展 `CommandContext` 或 `CommandRouter`，比如增加权限控制、冷却时间等。
