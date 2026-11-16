from argparse import Namespace
from datetime import timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "google-calendar"))
from google_api import Error
import service


START = "2026-11-17T20:00:00+08:00"
END = "2026-11-17T20:15:00+08:00"


class CalendarTest(unittest.TestCase):
    def test_timestamp_requires_an_offset_and_real_calendar_date(self):
        self.assertEqual(service.timestamp(START, "开始").astimezone(timezone.utc).hour, 12)
        for value in ("2026-11-17", "2026-11-17T20:00:00", "2026-11-31T20:00:00Z"):
            with self.subTest(value=value), self.assertRaises(Error):
                service.timestamp(value, "开始")

    def test_list_expands_occurrences_and_preserves_page_token(self):
        api = Mock()
        api.json.return_value = {"items": [{"id": "all_day", "start": {"date": "2026-11-17"}}],
                                 "nextPageToken": "next", "timeZone": "Asia/Singapore"}
        result = service.list_events(api, Namespace(start=START, end=END, query="测试", limit=10, page_token="first"))
        method, route = api.json.call_args.args
        self.assertEqual((method, route), ("GET", "/calendars/primary/events"))
        params = api.json.call_args.kwargs["params"]
        self.assertEqual(params["q"], "测试")
        self.assertEqual(params["singleEvents"], "true")
        self.assertEqual(params["pageToken"], "first")
        self.assertEqual(result["next_page_token"], "next")
        self.assertEqual(result["events"][0]["start"], {"date": "2026-11-17"})

    def test_invalid_range_and_result_count_stop_before_the_request(self):
        api = Mock()
        for start, end, limit in ((END, START, 20), (START, START, 20), (START, END, 101)):
            with self.subTest(start=start, end=end, limit=limit), self.assertRaises(Error):
                service.list_events(api, Namespace(start=start, end=end, limit=limit, query=None, page_token=None))
        api.json.assert_not_called()

    def test_create_quiet_posts_one_event_without_attendees(self):
        api = Mock()
        api.json.return_value = {"id": "event123", "summary": "测试", "start": {"dateTime": START}}
        result = service.create_event(api, Namespace(start=START, end=END, summary="测试", description=None, quiet=True))
        self.assertEqual(result["event_id"], "event123")
        method, route = api.json.call_args.args
        self.assertEqual((method, route), ("POST", "/calendars/primary/events"))
        args = api.json.call_args.kwargs
        self.assertEqual(args["params"]["sendUpdates"], "none")
        self.assertNotIn("attendees", args["body"])
        self.assertEqual(args["body"]["transparency"], "transparent")
        self.assertEqual(args["body"]["visibility"], "private")
        self.assertEqual(args["body"]["reminders"], {"useDefault": False})
        self.assertRegex(args["body"]["id"], r"^[0-9a-f]{32}$")

    def test_uncertain_write_provides_a_readback_id_and_does_not_retry(self):
        api = Mock()
        api.json.side_effect = Error("write_unverified", "test")
        with self.assertRaises(Error) as result:
            service.create_event(api, Namespace(start=START, end=END, summary="测试", description=None, quiet=False))
        self.assertEqual(result.exception.code, "write_unverified")
        self.assertEqual(api.json.call_count, 1)
        self.assertIn(api.json.call_args.kwargs["body"]["id"], result.exception.message)

    def test_read_validates_the_id(self):
        api = Mock()
        api.json.return_value = {"id": "test_event", "summary": "已读取"}
        self.assertEqual(service.read_event(api, Namespace(event_id="test_event"))["summary"], "已读取")
        api.json.assert_called_once_with("GET", "/calendars/primary/events/test_event", params={"fields": service.EVENT_FIELDS})
        with self.assertRaises(Error):
            service.read_event(api, Namespace(event_id="../other_calendar"))


if __name__ == "__main__":
    unittest.main()
