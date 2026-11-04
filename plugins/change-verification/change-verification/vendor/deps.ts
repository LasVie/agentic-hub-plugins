import path from 'node:path'
import { detectLanguage } from './heuristics.js'
import { collectRawReferences, extractDeclaredSymbols, extractStyleHooks } from './deps-refs.js'
import { pathHasSkippedSegment } from './skip-paths.js'
export interface SourceIndex { files: Map<string, string>; reverseDeps: Map<string, Set<string>> }
const INDEXED_EXT = /\.(kt|kts|java|swift|m|mm|h|dart|ts|tsx|mts|cts|js|jsx|mjs|cjs|vue|css|scss|sass|less|html?|xml|strings)$/i
function isGeneratedOrVendoredFile(rel: string): boolean {
  const base = path.posix.basename(rel.replace(/\\/g, '/'))
  if (/\.min\.(js|css)$/i.test(base)) return true
  if (/\.bundle\.(js|css)$/i.test(base)) return true
  if (/\.snap$/i.test(base)) return true
  return false
}

export function isIndexedSource(rel: string): boolean {
  const normalized = rel.replace(/\\/g, '/')
  if (pathHasSkippedSegment(normalized)) return false
  if (isGeneratedOrVendoredFile(normalized)) return false
  const lang = detectLanguage(normalized)
  if (lang === 'other') return false
  if (lang === 'resource') return /\.(xml|strings)$/i.test(normalized)
  return INDEXED_EXT.test(normalized)
}

function normalizeSpec(spec: string): string {
  return String(spec).replace(/^[./]*\//, '').replace(/\.(js|jsx|ts|tsx|mjs|cjs|mts|cts|vue|css|scss|sass|less|h|m|mm|dart|java|kt|kts|swift)$/i, '')
}

function specCandidates(spec: string): string[] {
  const base = normalizeSpec(spec)
  const exts = ['', '.ts', '.tsx', '.js', '.jsx', '.vue', '.dart', '.java', '.kt', '.swift', '.css', '.scss', '.h']
  const cands = new Set<string>()
  for (const e of exts) {
    cands.add(base + e)
    cands.add(base + '/index' + e)
  }
  return [...cands]
}

type PathLookup = {
  /** normalizeSpec(path) → concrete repo-relative paths */
  byNormalized: Map<string, string[]>
  /** basename without extension → concrete paths */
  byStem: Map<string, string[]>
}

function buildPathLookup(files: Map<string, string>): PathLookup {
  const byNormalized = new Map<string, string[]>()
  const byStem = new Map<string, string[]>()
  for (const f of files.keys()) {
    const nf = normalizeSpec(f)
    const nList = byNormalized.get(nf)
    if (nList) nList.push(f)
    else byNormalized.set(nf, [f])
    const stem = path.basename(f).replace(/\.[^.]+$/, '')
    const sList = byStem.get(stem)
    if (sList) sList.push(f)
    else byStem.set(stem, [f])
  }
  return { byNormalized, byStem }
}

function resolveSpecifier(spec: string, lookup: PathLookup): string[] {
  const out = new Set<string>()
  const addPath = (p: string) => {
    for (const c of specCandidates(p)) {
      for (const hit of lookup.byNormalized.get(normalizeSpec(c)) ?? []) {
        out.add(hit)
      }
    }
  }

  const pkg = spec.match(/^package:[^/]+\/(.+)$/)
  if (pkg) {
    addPath(pkg[1]!)
    addPath('lib/' + pkg[1]!)
    return [...out]
  }

  const clean = spec.split(/[?#]/)[0]!
  if (spec.startsWith('@/')) addPath(clean.slice(2))
  addPath(clean)
  return [...out]
}

export function buildIndexFromFileMap(files: Map<string, string>): SourceIndex {
  const reverseDeps = new Map<string, Set<string>>()
  const bySymbol = new Map<string, string[]>()
  /** hook token → stylesheets that declare it (avoids O(files×styles) scans). */
  const stylesByHook = new Map<string, string[]>()
  const lookup = buildPathLookup(files)
  /** Cache language detection across the three passes. */
  const langByRel = new Map<string, ReturnType<typeof detectLanguage>>()
  const langOf = (rel: string) => {
    let lang = langByRel.get(rel)
    if (lang === undefined) {
      lang = detectLanguage(rel)
      langByRel.set(rel, lang)
    }
    return lang
  }

  const ensure = (target: string) => {
    let set = reverseDeps.get(target)
    if (!set) {
      set = new Set()
      reverseDeps.set(target, set)
    }
    return set
  }

  // Pass 1: declared symbols and style hooks
  for (const [rel, content] of files) {
    const lang = langOf(rel)
    for (const sym of extractDeclaredSymbols(content, lang)) {
      const list = bySymbol.get(sym) ?? []
      list.push(rel)
      bySymbol.set(sym, list)
    }
    const hooks = extractStyleHooks(content, lang)
    if (hooks.size) {
      for (const h of hooks) {
        const list = stylesByHook.get(h)
        if (list) list.push(rel)
        else stylesByHook.set(h, [rel])
      }
    }
  }

  // Pass 2: references
  for (const [rel, content] of files) {
    const lang = langOf(rel)
    const raw = collectRawReferences(content, lang)
    const targets = new Set<string>()

    const fromDir = path.posix.dirname(rel.replace(/\\/g, '/'))
    const resolveRel = (spec: string): string[] => {
      if (spec.startsWith('@/')) {
        const tail = spec.slice(2)
        // Common web roots; exact match resolves if present, else src/ then lib/.
        return [tail, 'src/' + tail, 'lib/' + tail]
      }
      if (/^\.\.?\//.test(spec)) {
        return [
          path.posix
            .normalize(path.posix.join(fromDir, spec))
            .replace(/^\//, ''),
        ]
      }
      // Dart allows same-directory part/import without "./".
      if (lang === 'dart' && /^[A-Za-z0-9_.-]+$/.test(spec)) {
        return [path.posix.join(fromDir, spec)]
      }
      return [spec]
    }

    for (const spec of raw.specifiers) {
      if (/^[a-z]+:\/\//i.test(spec) && !spec.startsWith('package:')) continue
      for (const relSpec of resolveRel(spec)) {
        for (const t of resolveSpecifier(relSpec, lookup)) {
          if (t !== rel) targets.add(t)
        }
      }
    }
    for (const sym of raw.symbols) {
      // Vue kebab tag -> PascalCase symbol
      const variants = [sym]
      if (sym.includes('-')) {
        variants.push(
          sym
            .split('-')
            .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
            .join(''),
        )
      }
      for (const v of variants) {
        for (const t of bySymbol.get(v) ?? []) {
          if (t !== rel) targets.add(t)
        }
        // Also match by file stem (O(1) via precomputed index)
        for (const f of lookup.byStem.get(v) ?? []) {
          if (f !== rel) targets.add(f)
        }
      }
    }
    for (const t of targets) ensure(t).add(rel)
  }

  // Pass 3: style hooks usage -> stylesheet
  for (const [rel, content] of files) {
    const lang = langOf(rel)
    if (lang !== 'vue' && lang !== 'html' && lang !== 'javascript') continue
    const used = extractStyleHooks(content, lang)
    for (const h of used) {
      for (const styleFile of stylesByHook.get(h) ?? []) {
        if (styleFile !== rel) ensure(styleFile).add(rel)
      }
    }
  }

  return { files, reverseDeps }
}

export function rippleFrom(
  seeds: string[],
  reverseDeps: Map<string, Set<string>>,
  depth: number,
): Map<string, { depth: number; via: string }> {
  const result = new Map<string, { depth: number; via: string }>()
  const seedSet = new Set(seeds)
  let frontier = [...seeds]
  for (let d = 1; d <= depth; d++) {
    const next: string[] = []
    for (const file of frontier) {
      for (const importer of reverseDeps.get(file) ?? []) {
        if (seedSet.has(importer) || result.has(importer)) continue
        result.set(importer, { depth: d, via: file })
        next.push(importer)
      }
    }
    frontier = next
    if (!frontier.length) break
  }
  return result
}

