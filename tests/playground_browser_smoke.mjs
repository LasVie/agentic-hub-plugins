import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Use an installed Playwright package, or the task host's existing dependency bundle.
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYGROUND_PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const fixtures = resolve(root, 'tests/fixtures/playground');
const output = resolve(root, '.research/playground-functional');
await mkdir(output, { recursive: true });
const names = new Set(['product-card.html', 'data-explorer.html', 'document-critique.html']);
const server = createServer(async (request, response) => {
  const name = new URL(request.url, 'http://127.0.0.1').pathname.slice(1);
  if (!names.has(name)) { response.writeHead(404).end(); return; }
  try { response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }).end(await readFile(resolve(fixtures, name))); }
  catch { response.writeHead(500).end(); }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const origin = `http://127.0.0.1:${server.address().port}`;
const results = [];
const errors = [];
const externalRequests = [];
let browser;
let browserVersion;
let fatalError;
async function check(name, run) {
  try { await run(); results.push({ name, passed: true }); }
  catch (error) { results.push({ name, passed: false, error: error.message }); throw error; }
}
async function range(page, id, value) {
  await page.locator('#' + id).evaluate((element, next) => {
    element.value = String(next); element.dispatchEvent(new Event('input', { bubbles: true }));
  }, value);
}
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYGROUND_BROWSER_CHANNEL ? { channel: process.env.PLAYGROUND_BROWSER_CHANNEL } : {}) });
  browserVersion = browser.version();
  const context = await browser.newContext({ viewport: { width: 1280, height: 960 } });
  // Test both clipboard API outcomes without overwriting the user's OS clipboard.
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
      writeText: async text => { window.testClipboardText = text; },
    } });
  });
  await context.route('**/*', route => {
    const url = route.request().url();
    if (url.startsWith(origin + '/') || url.startsWith('file:') || url.startsWith('data:')) return route.continue();
    externalRequests.push(url); return route.abort();
  });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(origin + '/product-card.html');
  await check('design defaults and usable initial prompt', async () => {
    assert.equal(await page.locator('#card').evaluate(el => getComputedStyle(el).padding), '24px');
    assert.match(await page.locator('#prompt').inputValue(), /Lumen desk light/);
    assert.doesNotMatch(await page.locator('#prompt').inputValue(), /16px corner/);
  });
  await check('design control updates live preview and contextual prompt', async () => {
    await range(page, 'radius', 28);
    assert.equal(await page.locator('#card').evaluate(el => getComputedStyle(el).borderRadius), '28px');
    assert.match(await page.locator('#prompt').inputValue(), /28px corner radii/);
  });
  await check('all design presets synchronize controls and preview', async () => {
    for (const [name, padding, radius] of [['Bright', 32, 24], ['Compact', 16, 6], ['Quiet', 24, 16]]) {
      await page.getByRole('button', { name, exact: true }).click();
      assert.equal(await page.locator('#padding').inputValue(), String(padding));
      assert.equal(await page.locator('#radius').inputValue(), String(radius));
      assert.equal(await page.locator('#card').evaluate(el => getComputedStyle(el).padding), `${padding}px`);
    }
  });
  await check('design source-like input remains literal text', async () => {
    const input = '<img src=x onerror="window.injected=true">';
    await page.locator('#name').fill(input);
    assert.equal(await page.locator('#product-name').textContent(), input);
    assert.equal(await page.locator('#product-name img').count(), 0);
    assert.equal(await page.evaluate(() => window.injected), undefined);
  });
  await check('clipboard success branch copies the exact visible prompt (API stub)', async () => {
    await page.getByRole('button', { name: 'Quiet', exact: true }).click();
    await page.locator('#copy').click();
    assert.equal(await page.evaluate(() => window.testClipboardText), await page.locator('#prompt').inputValue());
    assert.match(await page.locator('#copy-status').textContent(), /Copied!/);
  });
  await page.screenshot({ path: resolve(output, 'product-card-desktop.png'), fullPage: true });
  await check('mobile design has no horizontal overflow and supports keyboard focus', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.locator('#radius').focus(); await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#radius').inputValue(), '17');
    await page.screenshot({ path: resolve(output, 'product-card-mobile.png'), fullPage: true });
  });
  await check('standalone design works over file URL while network is offline', async () => {
    await context.setOffline(true);
    await page.goto(pathToFileURL(resolve(fixtures, 'product-card.html')).href);
    await page.getByRole('button', { name: 'Bright', exact: true }).click();
    assert.equal(await page.locator('#padding').inputValue(), '32');
    assert.match(await page.locator('#prompt').inputValue(), /32px of padding/);
    await context.setOffline(false);
  });
  await check('clipboard denial selects text and does not claim success', async () => {
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw new Error('permission denied'); } } }));
    await page.locator('#copy').click();
    assert.match(await page.locator('#copy-status').textContent(), /copy it manually/);
    assert.doesNotMatch(await page.locator('#copy-status').textContent(), /Copied!/);
    assert.equal(await page.locator('#prompt').evaluate(el => el.selectionEnd - el.selectionStart), (await page.locator('#prompt').inputValue()).length);
  });
  await page.goto(origin + '/data-explorer.html');
  await check('data filters and preset update query and self-contained request', async () => {
    await page.getByRole('button', { name: 'High value', exact: true }).click();
    assert.match(await page.locator('#query').textContent(), /status = 'paid' AND total >= 100/);
    assert.match(await page.locator('#query').textContent(), /LIMIT 10/);
    assert.match(await page.locator('#prompt').inputValue(), /orders\(id INTEGER, status TEXT, total DECIMAL\)/);
  });
  await check('invalid numeric data blocks misleading output and recovers', async () => {
    await page.locator('#minimum').fill('-1');
    assert.equal(await page.locator('#copy').isDisabled(), true);
    assert.equal(await page.locator('#prompt').inputValue(), '');
    assert.match(await page.locator('#error').textContent(), /Enter a minimum/);
    await page.getByRole('button', { name: 'All orders', exact: true }).click();
    assert.equal(await page.locator('#copy').isDisabled(), false);
    assert.match(await page.locator('#query').textContent(), /LIMIT 25/);
  });
  await page.goto(origin + '/document-critique.html');
  await check('document source cannot execute embedded HTML', async () => {
    assert.match(await page.locator('#document').textContent(), /<img src=x/);
    assert.equal(await page.locator('#document img').count(), 0);
    assert.equal(await page.evaluate(() => window.injected), undefined);
    assert.equal(await page.locator('#copy').isDisabled(), true);
  });
  await check('document decisions separate approved changes from rejected context', async () => {
    await page.locator('[data-id="install"] [data-status="approved"]').click();
    await page.locator('[data-id="run"] [data-status="rejected"]').click();
    const prompt = await page.locator('#prompt').inputValue();
    const [approved, rejected] = prompt.split('Context only');
    assert.match(approved, /Line 3: Add the exact installation command/);
    assert.doesNotMatch(approved, /Show a complete run command/);
    assert.match(rejected, /do not apply these rejected suggestions/);
  });
  await check('review filters preserve decisions and literal user comments', async () => {
    await page.locator('#note-install').fill('<script>window.injected=true</script> Keep it short.');
    await page.locator('#filter').selectOption('rejected');
    assert.equal(await page.locator('[data-id="install"]').count(), 0);
    await page.locator('#filter').selectOption('all');
    assert.equal(await page.locator('[data-id="install"] [data-status="approved"]').getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('#prompt').inputValue(), /<script>window.injected=true<\/script>/);
    assert.equal(await page.evaluate(() => window.injected), undefined);
  });
  await page.screenshot({ path: resolve(output, 'document-critique-mobile.png'), fullPage: true });
  await check('no external network dependencies or browser JavaScript errors', async () => {
    assert.deepEqual(externalRequests, []); assert.deepEqual(errors, []);
  });
  await context.close();
} catch (error) {
  fatalError = error.message;
  console.error(error.stack || error.message); process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(done => server.close(done));
  const report = { tested_at: new Date().toISOString(), browser: `Playwright ${process.env.PLAYGROUND_BROWSER_CHANNEL || 'Chromium'}, headless`, browser_version: browserVersion, fatal_error: fatalError || null, scope: 'HTML produced by executing the ported skill workflow in the current Codex session; not target-host skill discovery or user acceptance', clipboard: 'Success and rejection tested with API stubs; OS clipboard untouched; actual browser permissions require manual testing', results, page_errors: errors, external_requests: externalRequests };
  await writeFile(resolve(output, 'browser-results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
}
