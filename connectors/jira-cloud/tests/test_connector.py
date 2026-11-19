import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def connector(slug):
    root = ROOT / slug / slug
    sys.path.insert(0, str(root))
    try:
        spec = importlib.util.spec_from_file_location(f"test_{slug}", root / "connector.py")
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value
    finally:
        sys.path.pop(0)


class ConnectorTests(unittest.TestCase):
    def test_jira_accessible_site_prompt(self):
        connector("jira-cloud")
        from browser_gate import site_options

        single_site = (b"\x1b[?25h\x1b[17DSelect the site to login \r\n"
                       b"1. https://test-site.atlassian.net\r\n"
                       b"There is only one option available; enter the number 1:")
        self.assertEqual(site_options(single_site), {"1": "test-site.atlassian.net"})
        self.assertEqual(site_options(single_site.split(b"There is")[0]), {})

        multiple_sites = (b"Select the site to login\n1. https://first.atlassian.net\n"
                          b"2. https://second.atlassian.net/\nEnter a number between 1 and 2: ")
        self.assertEqual(site_options(multiple_sites), {"1": "first.atlassian.net", "2": "second.atlassian.net"})
        self.assertEqual(site_options(multiple_sites.replace(b".atlassian.net", b".example.com")), {})

    def test_jira(self):
        m = connector("jira-cloud")
        args = argparse.Namespace(command="create", container="QA", title="测试", body="正文", type="Task")
        self.assertEqual(m.select_command(args), ["jira", "workitem", "create", "--project", "QA",
                          "--type", "Task", "--summary", "测试", "--description", "正文"])
        with self.assertRaises(m.ConnectorError):
            m.select_command(argparse.Namespace(command="read", id="--help"))
        self.assertEqual(m.select_command(argparse.Namespace(command="read", id="QA-7"))[-1], "QA-7")
