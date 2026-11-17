"""Behavioral tests of this plugin's owned lifecycle and real loopback HTTP.

Cancellation races use an explicit deterministic plugin-local engine stub; they
prove request fencing, not CoolProp numerical execution. The separately gated
numeric HTTP test uses the real engine after source/license clearance.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import http.client
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

PAYLOAD = Path(os.environ.get('STEAM_PAYLOAD', Path(__file__).resolve().parents[1] / 'offline-steam-properties-workbench'))
sys.dont_write_bytecode = True

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

runtime = module('_steam_test_runtime', PAYLOAD / 'runtime/runtime.py')
server_module = module('_steam_test_server', PAYLOAD / 'runtime/server.py')


def chinese(message):
    return isinstance(message, str) and any('\u4e00' <= c <= '\u9fff' for c in message)


@contextmanager
def serving(directory):
    state = {'token': secrets.token_hex(32), 'session_id': secrets.token_hex(16),
             'state_dir': str(directory)}
    server = server_module.WorkbenchServer(state)
    server.timeout = .05
    def loop():
        while not server.stopping.is_set():
            server.handle_request()
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.stop()
        thread.join(2)
        server.server_close()
        if thread.is_alive():
            raise AssertionError('Owned HTTP loop did not stop')


def request(server, route, body=None, *, raw=None, headers=None, token=None):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=20)
    values = {'Content-Type': 'application/json'} if body is not None or raw is not None else {}
    values.update(headers or {})
    data = raw if raw is not None else json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    try:
        connection.request('POST' if data is not None else 'GET',
                           f'/{token or server.token}/{route}', body=data, headers=values)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def decoded(answer):
    status, headers, data = answer
    return status, json.loads(data)


class OwnedLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='steam-runtime-')
        self.workspace = Path(self.temporary.name).resolve()

    def tearDown(self):
        runtime.lifecycle({'action': 'stop', 'workspace': str(self.workspace), 'confirmed': True})
        self.temporary.cleanup()

    def life(self, action, **extra):
        return runtime.lifecycle({'action': action, 'workspace': str(self.workspace), **extra})

    def test_authorization_reuse_stop_and_restart(self):
        self.assertFalse(self.life('status')['running'])
        for action in ['start', 'stop']:
            result = self.life(action)
            self.assertFalse(result['ok']); self.assertTrue(chinese(result['error']['message']))
        first = self.life('start', confirmed=True)
        self.assertTrue(first['ok'] and first['running'])
        again = self.life('start', confirmed=True)
        self.assertEqual(first['url'], again['url']); self.assertFalse(again['started'])
        self.assertEqual(self.life('status')['session_id'], first['session_id'])
        self.assertFalse(self.life('stop', confirmed=True)['running'])
        self.assertFalse(self.life('status')['running'])
        second = self.life('start', confirmed=True)
        self.assertNotEqual(second['session_id'], first['session_id'])
        self.assertFalse(self.life('stop', confirmed=True)['running'])

    def test_unowned_nonprivate_symlink_and_corrupt_state_are_preserved(self):
        directory = runtime.runtime_dir(self.workspace, create=True)
        directory.chmod(0o755)
        self.assertFalse(self.life('start', confirmed=True)['ok'])
        self.assertEqual(directory.stat().st_mode & 0o777, 0o755)
        directory.chmod(0o700)
        state = directory / 'server.json'
        original = b'{"broken":true}'
        state.write_bytes(original); state.chmod(0o600)
        self.assertFalse(self.life('start', confirmed=True)['ok'])
        self.assertFalse(self.life('stop', confirmed=True)['ok'])
        self.assertEqual(state.read_bytes(), original)
        state.unlink()
        target = self.workspace / 'protected-evidence.json'
        target.write_bytes(b'unchanged'); target.chmod(0o600); state.symlink_to(target)
        self.assertFalse(self.life('start', confirmed=True)['ok'])
        self.assertTrue(state.is_symlink()); self.assertEqual(target.read_bytes(), b'unchanged')
        alias = self.workspace / 'workspace-alias'; alias.symlink_to(self.workspace, target_is_directory=True)
        self.assertFalse(runtime.lifecycle({'action': 'status', 'workspace': str(alias)})['ok'])

    def test_invalid_saved_project_recovers_with_original_backup(self):
        directory = runtime.runtime_dir(self.workspace, create=True)
        original = b'{"not":"a valid project"}'
        target = directory / 'project.json'; target.write_bytes(original); target.chmod(0o600)
        project, warnings = runtime.load_project(directory)
        self.assertTrue(warnings and chinese(warnings[0])); self.assertEqual(target.read_bytes(), original)
        self.assertEqual(project, runtime.model.examples()['常压饱和水'])
        project['name'] = '恢复后的中文项目'
        runtime.save_project(directory, project)
        backups = list(directory.glob('project.invalid-*.json'))
        self.assertEqual(len(backups), 1); self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(runtime.load_project(directory), (project, []))

    def test_foreign_loopback_identity_is_never_stopped(self):
        directory = runtime.runtime_dir(self.workspace, create=True)
        with serving(directory) as foreign:
            state = {'version': runtime.VERSION, 'root': str(runtime.ROOT), 'port': foreign.server_port,
                     'token': foreign.token, 'session_id': secrets.token_hex(16)}
            runtime._save_state(directory, state)
            before = (directory / 'server.json').read_bytes()
            self.assertFalse(self.life('stop', confirmed=True)['ok'])
            self.assertFalse(foreign.stopping.is_set())
            self.assertEqual((directory / 'server.json').read_bytes(), before)


class LoopbackHttpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='steam-http-')
        self.workspace = Path(self.temporary.name).resolve()
        self.directory = server_module.runtime.runtime_dir(self.workspace, create=True)
        self.context = serving(self.directory); self.server = self.context.__enter__()
        self.project = copy.deepcopy(runtime.model.examples()['常压饱和水'])

    def tearDown(self):
        self.context.__exit__(None, None, None); self.temporary.cleanup()

    def test_tokens_host_origin_fetch_boundary_and_static_modules(self):
        server = self.server
        self.assertEqual(request(server, 'api/health')[0], 200)
        self.assertEqual(request(server, 'api/health', token='bad-token')[0], 404)
        self.assertEqual(request(server, 'api/health', headers={'Host': 'foreign.invalid'})[0], 403)
        self.assertEqual(request(server, 'api/health', headers={'Origin': 'https://foreign.invalid'})[0], 403)
        self.assertEqual(request(server, 'api/health', headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)
        navigation = {'Sec-Fetch-Site': 'cross-site', 'Sec-Fetch-Mode': 'navigate',
                      'Sec-Fetch-Dest': 'document', 'Sec-Fetch-User': '?1'}
        self.assertEqual(request(server, 'index.html', headers=navigation)[0], 200)
        for asset in ['index.html', 'app.js', 'ui_helpers.mjs', 'style.css']:
            status, headers, data = request(server, asset)
            self.assertEqual(status, 200, asset); self.assertTrue(data)
            self.assertIn("default-src 'none'", headers['Content-Security-Policy'])
            self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
        self.assertEqual(request(server, '../runtime/runtime.py')[0], 404)
        self.assertEqual(request(server, 'api/unknown', {})[0], 404)

    def test_malformed_extra_nonfinite_and_huge_inputs_fail_without_saving(self):
        for raw in [b'{"request_id":"a","request_id":"b"}', b'{"x":NaN}', b'[]']:
            status, result = decoded(request(self.server, 'api/calculate', raw=raw))
            self.assertEqual(status, 400); self.assertFalse(result['ok'])
            self.assertTrue(chinese(result['error']['message']))
        for changes in [{'script': 'never execute'}, {'state': {'pair': 'PQ', 'pressure_pa': 10**400, 'quality': 0}}]:
            project = {**self.project, **changes}
            status, result = decoded(request(self.server, 'api/calculate', {'request_id': secrets.token_hex(8), 'project': project}))
            self.assertEqual(status, 400); self.assertFalse(result['ok'])
            self.assertTrue(chinese(result['error']['message']))
        self.assertFalse((self.directory / 'project.json').exists())
        status, _ = decoded(request(self.server, 'api/project', raw=b'{}',
                                   headers={'Content-Length': str(runtime.MAX_INPUT + 1025)}))
        self.assertEqual(status, 400)

    def test_saved_project_reset_and_fresh_server_reload(self):
        self.project['name'] = '重载验证中文项目'
        self.assertEqual(decoded(request(self.server, 'api/project', {'project': self.project}))[1]['project'], self.project)
        self.context.__exit__(None, None, None)
        self.context = serving(self.directory); self.server = self.context.__enter__()
        initial = decoded(request(self.server, 'api/initial'))[1]
        self.assertEqual(initial['project'], self.project); self.assertIsNone(initial['result'])
        self.assertEqual(decoded(request(self.server, 'api/reset', {}))[1]['project'], runtime.model.examples()['常压饱和水'])
        self.assertEqual(decoded(request(self.server, 'api/initial'))[1]['project'], runtime.model.examples()['常压饱和水'])

    def test_cancel_before_calculate_fences_late_request_without_engine(self):
        request_id = 'cancelled-before-post'
        status, result = decoded(request(self.server, 'api/cancel', {'request_id': request_id}))
        self.assertEqual(status, 200); self.assertTrue(result['cancellation_recorded'])
        with patch.object(server_module.runtime, 'run_engine', side_effect=AssertionError('Late job must never execute')):
            status, result = decoded(request(self.server, 'api/calculate', {'request_id': request_id, 'project': self.project}))
        self.assertEqual(status, 409); self.assertTrue(result['cancelled'])
        self.assertFalse((self.directory / 'project.json').exists())

    def test_busy_wrong_id_cancel_and_late_result_are_fenced(self):
        entered = threading.Event(); answers = []
        def controlled_engine(project, cancelled):
            entered.set()
            if not cancelled.wait(3): raise AssertionError('Matching cancellation did not reach active owned job')
            return runtime.failure('计算已取消。', cancelled=True)
        with patch.object(server_module.runtime, 'run_engine', side_effect=controlled_engine):
            worker = threading.Thread(target=lambda: answers.append(decoded(request(self.server, 'api/calculate',
                {'request_id': 'active-job', 'project': self.project}))))
            worker.start()
            try:
                self.assertTrue(entered.wait(2))
                self.assertEqual(decoded(request(self.server, 'api/calculate', {'request_id': 'second-job', 'project': self.project}))[0], 409)
                wrong = decoded(request(self.server, 'api/cancel', {'request_id': 'wrong-job'}))[1]
                self.assertFalse(wrong['cancelled'])
                self.assertTrue(decoded(request(self.server, 'api/health'))[1]['busy'])
                self.assertTrue(decoded(request(self.server, 'api/cancel', {'request_id': 'active-job'}))[1]['cancelled'])
            finally:
                if worker.is_alive(): request(self.server, 'api/cancel', {'request_id': 'active-job'})
                worker.join(4)
            self.assertFalse(worker.is_alive()); self.assertEqual(len(answers), 1)
            self.assertTrue(answers[0][1]['cancelled']); self.assertFalse(answers[0][1]['ok'])
            self.assertFalse(decoded(request(self.server, 'api/health'))[1]['busy'])
            self.assertEqual(decoded(request(self.server, 'api/calculate', {'request_id': 'active-job', 'project': self.project}))[0], 409)

    def test_authenticated_shutdown_acknowledges_and_stops_owned_server(self):
        status, result = decoded(request(self.server, 'api/shutdown', {}))
        self.assertEqual(status, 200); self.assertFalse(result['running'])
        self.assertTrue(self.server.stopping.wait(1))

    @unittest.skipUnless(os.environ.get('STEAM_TEST_ENGINE_READY') == '1', 'CoolProp binary/source gate not cleared for this run')
    def test_real_numeric_http_result_matches_current_input_and_water_fixture(self):
        status, result = decoded(request(self.server, 'api/calculate', {'request_id': 'real-water', 'project': self.project}))
        self.assertEqual(status, 200); self.assertTrue(result['ok'], result)
        self.assertEqual(result['input'], self.project); self.assertEqual(result['request_id'], 'real-water')
        self.assertAlmostEqual(result['state']['temperature_k'], 373.1243, delta=.02)
        self.assertAlmostEqual(result['saturation']['latent_heat_j_kg'], 2256471.6, delta=300)
        self.assertEqual(len(result['sweep']), self.project['sweep']['points'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
