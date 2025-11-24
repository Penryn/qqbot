from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openpyxl import load_workbook

from ... import config
from ...client import OneBotClient


@dataclass
class BirthdayEntry:
    name: str
    month: int
    day: int
    group_id: Optional[int]
    user_id: Optional[int]
    message: str

    def is_today(self, today: date) -> bool:
        return self.month == today.month and self.day == today.day

    def key(self, today: date) -> Tuple[int, int, str]:
        return (today.month, today.day, self.name)


def _parse_md(value: Any) -> Optional[Tuple[int, int]]:
    """Parse month/day from various cell values."""

    if value is None:
        return None

    if isinstance(value, datetime):
        value = value.date()

    if isinstance(value, date):
        return (value.month, value.day)

    if isinstance(value, str):
        text = value.strip()
        # Supports "MM-DD" or "YYYY-MM-DD"
        parts = text.split("-")
        if len(parts) == 2:
            try:
                m, d = int(parts[0]), int(parts[1])
                return (m, d)
            except ValueError:
                return None
        if len(parts) == 3:
            try:
                _, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                return (m, d)
            except ValueError:
                return None
    return None


def _normalize_header(name: Any) -> str:
    return str(name or "").strip().lower()


def load_birthdays(path: str | Path) -> List[BirthdayEntry]:
    """
    Load birthday entries from an Excel file.

    Expected header fields (case-insensitive, with Chinese aliases):
    - name / 姓名 (required)
    - date / 生日 / 出生日期 (required): YYYY-MM-DD or MM-DD or Excel date
    - user_id / qq / qq号 (optional, 私聊发送)
    - message / 祝福语 (optional): fallback to default template
    """

    file_path = Path(path)
    if not file_path.exists():
        if config.DEBUG:
            print(f"[birthday] file not found: {file_path}")
        return []

    wb = load_workbook(file_path, data_only=True)
    sheet = wb.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    header_raw = rows[0]
    header_norm = [_normalize_header(h) for h in header_raw]
    header_map: Dict[str, int] = {name: idx for idx, name in enumerate(header_norm) if name}

    aliases: Dict[str, List[str]] = {
        "name": ["name", "姓名"],
        "date": ["date", "生日", "出生日期", "出生"],
        "message": ["message", "祝福语", "祝福"],
    }

    def col(*names: str) -> Optional[int]:
        for n in names:
            if n in header_map:
                return header_map[n]
        return None

    name_col = col(*aliases["name"])
    date_col = col(*aliases["date"])

    if name_col is None or date_col is None:
        if config.DEBUG:
            print("[birthday] missing required columns: name/date")
        return []

    entries: List[BirthdayEntry] = []
    for row in rows[1:]:
        name_val = row[name_col] if name_col is not None else None
        date_val = row[date_col] if date_col is not None else None
        if not name_val or date_val is None:
            continue

        md = _parse_md(date_val)
        if md is None:
            continue
        month, day = md

        msg_col = col(*aliases["message"])

        message_val = row[msg_col] if msg_col is not None else None

        group_id = config.BIRTHDAY_DEFAULT_GROUP_ID
        msg = str(message_val) if message_val is not None else f"生日快乐，{name_val}！"

        # 只群发：必须有默认群号
        if group_id is None:
            continue

        entries.append(
            BirthdayEntry(
                name=str(name_val),
                month=month,
                day=day,
                group_id=group_id,
                user_id=None,
                message=msg,
            )
        )

    return entries


async def _send_greeting(client: OneBotClient, entry: BirthdayEntry) -> None:
    """Send birthday greeting to group or private target."""

    if entry.group_id:
        await client.send_group_message(entry.group_id, entry.message)


_sent_today: set[Tuple[int, int, str]] = set()
_last_date: Optional[date] = None


async def check_and_send_birthdays(client: OneBotClient) -> None:
    """
    Single-run birthday check. Intended to be called periodically by a scheduler.

    - Uses in-process memory to avoid duplicate sends per day.
    - Resets the cache when日期 changes。
    """

    global _last_date, _sent_today

    today = date.today()
    if _last_date != today:
        _sent_today = set()
        _last_date = today

    entries = load_birthdays(config.BIRTHDAY_XLSX_PATH)
    for entry in entries:
        if entry.is_today(today):
            key = entry.key(today)
            if key in _sent_today:
                continue
            try:
                await _send_greeting(client, entry)
                _sent_today.add(key)
                if config.DEBUG:
                    print(f"[birthday] sent greeting to {entry.name}")
            except Exception as e:  # noqa: BLE001
                if config.DEBUG:
                    print(f"[birthday] failed to send greeting: {e!r}")
