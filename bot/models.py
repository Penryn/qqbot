from __future__ import annotations

from typing import Any, Dict, Optional
from typing import Literal

from pydantic import BaseModel


class OneBotEvent(BaseModel):
    """通用的 OneBot v11 事件基类（只保留常用字段）"""

    time: Optional[int] = None
    # LLOneBot 这里实际发的是数字 QQ 号，所以兼容 int 和 str
    self_id: Optional[int | str] = None
    post_type: str
    # message / meta_event / notice / request ...


class MessageSender(BaseModel):
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    card: Optional[str] = None


class MessageEvent(OneBotEvent):
    """群聊/私聊消息事件（只覆盖常用字段）"""

    # 在 pydantic v2 中使用 Literal 固定取值
    post_type: Literal["message"] = "message"
    message_type: str  # "private" / "group"
    sub_type: Optional[str] = None
    message_id: Optional[int] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    raw_message: str
    message: Any
    sender: Optional[MessageSender] = None


class SendMessageAction(BaseModel):
    """发送消息的动作 payload（用于方便构造）"""

    action: str  # e.g. "send_group_msg" / "send_private_msg"
    params: Dict[str, Any]
    echo: Optional[str] = None
