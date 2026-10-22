// Collect actual installed license/NOTICE texts; this is evidence, not automatic permission approval.
import { readdir, readFile, mkdir, writeFile, realpath } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('.', import.meta.url));
const seen = new Set();
const entries = [];
async function scan(dir) {
  let items;
  try { items = await readdir(dir, { withFileTypes: true }); }
  catch (error) { if (error.code === 'ENOENT') return; throw error; }
  for (const item of items) {
    if (item.name.startsWith('.')) continue;
    const pkg = join(dir, item.name);
    if (item.name.startsWith('@')) { await scan(pkg); continue; }
    if (!item.isDirectory() && !item.isSymbolicLink()) continue;
    const actual = await realpath(pkg);
    if (seen.has(actual)) continue;
    seen.add(actual);
    let meta;
    try { meta = JSON.parse(await readFile(join(pkg, 'package.json'), 'utf8')); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    if (!meta.name || !meta.version) throw new Error('Package identity missing: ' + pkg);
    const destination = 'licenses/npm/' + meta.name.replace(/[^a-zA-Z0-9._-]/g, '_') + '@' + meta.version;
    await mkdir(join(root, destination), { recursive: true });
    const evidence = [];
    for (const file of await readdir(pkg, { withFileTypes: true })) {
      if (file.isFile() && /^(licen[cs]e|copying|notice)(\.|$)/i.test(file.name)) {
        await writeFile(join(root, destination, file.name), await readFile(join(pkg, file.name)));
        evidence.push(destination + '/' + file.name);
      }
    }
    entries.push({ name: meta.name, version: meta.version, declared_license: meta.license ?? null, evidence });
    await scan(join(pkg, 'node_modules'));
  }
}
await scan(join(root, 'node_modules'));
entries.sort((a, b) => a.name.localeCompare(b.name) || a.version.localeCompare(b.version));
await writeFile(join(root, 'DEPENDENCY_LICENSES.json'), JSON.stringify({
  automatic_collection_only: true,
  note: 'Read each full text and scope; package metadata may be incomplete. Preserve this directory in distributions.',
  packages: entries,
}, null, 2) + '\n');
console.log('Collected installed license/NOTICE evidence for ' + entries.length + ' packages');
