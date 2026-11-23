"""List, create and read Google Calendar events on the user's primary calendar."""
from __future__ import annotations

from datetime import datetime
import re
from uuid import uuid4

SLUG = "google-calendar"
LABEL = "Google 日历连接器"
SCOPE = "https://www.googleapis.com/auth/calendar.events.owned"
BASE = "https://www.googleapis.com/calendar/v3"
EVENTS = "/calendars/primary/events"
EVENT_FIELDS = "id,summary,start,end,status,description,htmlLink"
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\Z")


def timestamp(value, label):
    from google_api import invalid

    if TIMESTAMP.fullmatch(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    raise invalid(f"{label}须包含日期、时间和时区偏移，格式如 2026-11-17T20:00:00+08:00。")


def validate_range(start, end):
    from google_api import invalid

    if timestamp(start, "开始时间") >= timestamp(end, "结束时间"):
        raise invalid("结束时间须晚于开始时间。")


def event_data(event):
    return {
        "event_id": event["id"],
        "summary": event.get("summary", ""),
        "start": event.get("start", {}),
        "end": event.get("end", {}),
        "status": event.get("status"),
        "description": event.get("description", ""),
        "url": event.get("htmlLink"),
    }


def list_events(api, args):
    from google_api import invalid, text

    validate_range(args.start, args.end)
    if not 1 <= args.limit <= 100:
        raise invalid("结果数须为 1 至 100。")
    params = {
        "timeMin": args.start, "timeMax": args.end, "singleEvents": "true", "orderBy": "startTime",
        "showDeleted": "false", "maxResults": args.limit,
        "fields": f"items({EVENT_FIELDS}),nextPageToken,timeZone",
    }
    if args.query is not None:
        params["q"] = text(args.query, "关键词", 300)
    if args.page_token is not None:
        params["pageToken"] = text(args.page_token, "分页标识", 2048)
    result = api.json("GET", EVENTS, params=params)
    return {
        "calendar": "primary", "time_zone": result.get("timeZone"),
        "events": [event_data(event) for event in result.get("items", [])],
        "next_page_token": result.get("nextPageToken"),
    }


def read_event(api, args):
    from google_api import opaque

    event_id = opaque(args.event_id, "日程标识")
    return event_data(api.json("GET", f"{EVENTS}/{event_id}", params={"fields": EVENT_FIELDS}))


def create_event(api, args):
    from google_api import Error, text

    validate_range(args.start, args.end)
    body = {
        "id": uuid4().hex, "summary": text(args.summary, "日程标题", 300),
        "start": {"dateTime": args.start}, "end": {"dateTime": args.end},
    }
    if args.description is not None:
        body["description"] = text(args.description, "日程描述", 3500, multiline=True, allow_empty=True)
    if args.quiet:
        body.update(visibility="private", transparency="transparent", reminders={"useDefault": False})
    try:
        result = api.json("POST", EVENTS, params={"sendUpdates": "none", "fields": EVENT_FIELDS}, body=body)
        return event_data(result)
    except (Error, KeyError, TypeError) as exc:
        if isinstance(exc, Error) and exc.code != "write_unverified":
            raise
        raise Error("write_unverified", f"请先回读日程 {body['id']} 核对写入结果。") from None


def register(commands):
    listing = commands.add_parser("list", help="按时间范围和关键词查询主日历")
    create = commands.add_parser("create", help="在主日历创建单次日程")
    for command in (listing, create):
        command.add_argument("--from", dest="start", required=True, help="开始时间，带时区的 RFC 3339")
        command.add_argument("--to", dest="end", required=True, help="结束时间，带时区的 RFC 3339")
    listing.add_argument("--query", help="日程搜索关键词")
    listing.add_argument("--limit", type=int, default=30, help="最多返回的日程数")
    listing.add_argument("--page-token", help="上次查询返回的下一页标识")
    listing.set_defaults(operation=list_events)
    create.add_argument("--summary", required=True, help="日程标题")
    create.add_argument("--description", help="日程描述")
    create.add_argument("--quiet", action="store_true", help="设为私密、空闲且无提醒")
    create.set_defaults(operation=create_event)

    read = commands.add_parser("read", help="按标识读取一条日程")
    read.add_argument("--event-id", required=True, help="查询或创建返回的日程标识")
    read.set_defaults(operation=read_event)
