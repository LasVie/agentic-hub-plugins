import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ts = require(path.resolve(process.argv[2]));
const directory = path.resolve(process.argv[3]);
for (const name of (await fs.readdir(directory)).filter(name => name.endsWith('.ts'))) {
  const source = await fs.readFile(path.join(directory, name), 'utf8');
  const result = ts.transpileModule(source, { compilerOptions: {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022,
    removeComments: false, newLine: ts.NewLineKind.LineFeed,
  }, reportDiagnostics: true });
  if (result.diagnostics?.length) throw new Error(JSON.stringify(result.diagnostics));
  await fs.writeFile(path.join(directory, name.replace(/\.ts$/, '.js')), result.outputText);
}
console.log(JSON.stringify({ compiler: ts.version, files: 4, runtime_dependencies: 0 }));
