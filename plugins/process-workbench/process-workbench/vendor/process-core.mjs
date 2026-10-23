// Adapted 2026-10-23 from weibaohui/dsh-process src/validate.js (MIT).
// CHANGES: retain only object metadata/flow helpers; omit YAML and host integration.
const FLOW_KEYWORDS = new Set(['next','end','break']);
const isMap = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const isNonEmptyString = v => typeof v === 'string' && v.trim() !== '';
function flowTarget(value) {
  if (typeof value !== 'string') return null
  const v = value.trim()
  if (v === '' || FLOW_KEYWORDS.has(v)) return null
  return v.startsWith('goto:') ? v.slice(5).trim() : v
}

function extractMeta(data) {
  const p = isMap(data) && isMap(data.process) ? data.process : {}
  const phases = isMap(data) && Array.isArray(data.phases) ? data.phases : []
  let linkCount = 0
  for (const ph of phases) if (isMap(ph) && Array.isArray(ph.links)) linkCount += ph.links.length
  return {
    name: isNonEmptyString(p.name) ? p.name.trim() : '',
    guid: typeof p.guid === 'string' ? p.guid : '',
    display_name: isNonEmptyString(p.display_name) ? p.display_name.trim() : '',
    description: typeof p.description === 'string' ? p.description.trim() : '',
    category: isNonEmptyString(p.category) ? p.category.trim() : '',
    complexity: isNonEmptyString(p.complexity) ? p.complexity.trim() : '',
    version: p.version === undefined || p.version === null ? '' : String(p.version),
    phaseCount: phases.length,
    linkCount,
  }
}

export {flowTarget,extractMeta};
