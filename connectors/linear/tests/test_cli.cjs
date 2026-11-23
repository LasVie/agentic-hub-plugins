'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {runBounded, safeFailure, runtimeModule, inputFile} = require('../linear/skills/linear-guide/scripts/linear-cli.cjs');
const {argumentError, visibleTool} = require('../linear/skills/linear-guide/scripts/scope.cjs');
async function listen(server, port = 0) {
  await new Promise((resolve, reject) => {server.once('error', reject); server.listen(port, '127.0.0.1', resolve);});
  return server.address().port;
}
async function close(server) { await new Promise(resolve => server.close(resolve)); }

test('操作成功返回前，子进程已退出并释放 TCP 端口', {timeout: 3000}, async () => {
  const code = "const s=require('node:net').createServer();s.listen(0,'127.0.0.1',()=>{console.log(JSON.stringify({port:s.address().port}));s.close(()=>process.exit(0))})";
  const result = await runBounded(process.execPath, ['-e', code], {timeoutMs: 1000});
  assert.equal(result.code, 0);
  const server = net.createServer();
  await listen(server, JSON.parse(result.stdout).port);
  await close(server);
});
test('忽略 SIGTERM 的操作超时后强制退出，端口可重用', {timeout: 4000}, async () => {
  const reservation = net.createServer();
  const port = await listen(reservation); await close(reservation);
  const code = "process.on('SIGTERM',()=>{});require('node:net').createServer().listen(" + port + ",'127.0.0.1')";
  await assert.rejects(runBounded(process.execPath, ['-e', code], {timeoutMs: 200, graceMs: 50}), {code: 'TIMEOUT'});
  const server = net.createServer(); await listen(server, port); await close(server);
});
test('宿主终止 CLI 时，CLI 会结束其操作子进程并释放端口', {timeout: 4000}, async () => {
  const reservation = net.createServer();
  const port = await listen(reservation); await close(reservation);
  const childCode = "require('node:net').createServer().listen(" + port + ",'127.0.0.1',()=>process.send({type:'ready'}))";
  const modulePath = require.resolve('../linear/skills/linear-guide/scripts/linear-cli.cjs');
  const parentCode = 'const {runBounded}=require(' + JSON.stringify(modulePath) + ');runBounded(process.execPath,[\'-e\',' + JSON.stringify(childCode) + '],{timeoutMs:2000,onProgress:m=>{if(m.type===\'ready\')console.log(\'ready\')}}).catch(e=>console.log(e.code))';
  const parent = spawn(process.execPath, ['-e', parentCode], {stdio: ['ignore','pipe','ignore']});
  try {
    const [data] = await once(parent.stdout, 'data');
    assert.match(data.toString(), /ready/);
    const exited = once(parent, 'exit');
    parent.kill('SIGTERM');
    await exited;
    const server = net.createServer(); await listen(server, port); await close(server);
  } finally {if (parent.exitCode === null && parent.signalCode === null) parent.kill('SIGKILL');}
});
test('未知错误不泄露原始异常，写入中断要求先回读', () => {
  const e = Object.assign(new Error('private-token-must-not-appear'), {writeAttempted: true});
  const result = safeFailure(e);
  assert.equal(result.writeOutcome, 'unknown');
  assert.match(result.recovery, /先.*回读/);
  assert.doesNotMatch(JSON.stringify(result), /private-token/);
});
test('UTF-8 中文被拆成多段输出时保持原文', async () => {
  const code = "const b=Buffer.from('中文回读');process.stdout.write(b.subarray(0,2));setTimeout(()=>process.stdout.write(b.subarray(2)),20)";
  const result = await runBounded(process.execPath, ['-e', code], {timeoutMs: 1000});
  assert.equal(result.stdout, '中文回读');
});
test('拒绝错误版本或被替换的客户端模块', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'linear-module-test-'));
  try {
    fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({name: 'mcp-remote', version: '0.16.5'}));
    assert.throws(() => runtimeModule(root), {code: 'RUNTIME_MISSING'});
    fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({name: 'mcp-remote', version: '0.16.6'}));
    fs.mkdirSync(path.join(root, 'dist'));
    fs.writeFileSync(path.join(root, 'dist/chunk-MKB2ICYW.js'), 'altered module');
    assert.throws(() => runtimeModule(root), {code: 'RUNTIME_MISMATCH'});
  } finally {fs.rmSync(root, {recursive: true, force: true});}
});
test('JSON 参数文件在连接前拒绝修改已有工单', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'linear-input-test-'));
  try {
    const file = path.join(root, 'input.json');
    fs.writeFileSync(file, JSON.stringify({team: 'OPE', title: '中文测试', id: 'OPE-6'}));
    assert.throws(() => inputFile(['call', 'save_issue', '--input-file', file]), {code: 'SCOPE_REJECTED'});
    fs.writeFileSync(file, JSON.stringify({team: 'OPE', title: '中文测试'}));
    assert.equal(inputFile(['call', 'save_issue', '--input-file', file]).arguments.title, '中文测试');
  } finally {fs.rmSync(root, {recursive: true, force: true});}
});
test('未知及删除工具默认拒绝，创建与评论保持原范围', () => {
  for (const name of ['delete_issue', 'save_project', 'future_tool', '__proto__']) assert.equal(typeof argumentError(name, {}), 'string');
  assert.equal(argumentError('save_issue', {team: 'OPE', title: '测试'}), null);
  assert.equal(argumentError('save_comment', {issueId: 'OPE-7', body: '测试'}), null);
  for (const args of [{id: 'comment', issueId: 'OPE-7', body: '修改'}, {projectId: 'x', body: '跨对象'}]) assert.equal(typeof argumentError('save_comment', args), 'string');
});
test('中文工具说明不扩大原始创建 schema', () => {
  const t = visibleTool({name: 'save_issue', inputSchema: {type: 'object', properties: {team: {type: 'string'}, title: {type: 'string'}, id: {type: 'string'}}}});
  assert.deepEqual(Object.keys(t.inputSchema.properties), ['team','title']);
  assert.deepEqual(t.inputSchema.required, ['team','title']);
  assert.equal(t.inputSchema.additionalProperties, false);
  assert.match(t.description, /新/);
});
