// Adapted 2026-10-23 from webkubor/dsh-env-inspector lib/index.js (MIT).
// CHANGES: extract pure listening-port parser, omit DSH core-port exemptions (read-only).
const DSH_CORE_PORT_SET = new Set();
export function parseListeningPorts(stdout) {
	if (typeof stdout !== 'string' || stdout.trim().length === 0) return []
	const lines = stdout.trim().split('\n')
	const map = new Map()

	for (let i = 1; i < lines.length; i++) {
		const line = lines[i].trim()
		if (!line) continue
		const parts = line.split(/\s+/)
		if (parts.length < 9) continue
		const command = parts[0]
		const pid = parseInt(parts[1], 10)
		const nameField = parts[parts.length - 2]
		if (!nameField) continue

		const lastColon = nameField.lastIndexOf(':')
		if (lastColon === -1) continue
		const host = nameField.slice(0, lastColon)
		const portStr = nameField.slice(lastColon + 1)
		const port = parseInt(portStr, 10)
		if (Number.isNaN(port) || port <= 0 || port > 65535) continue

		const isWildcard = host === '*' || host === '0.0.0.0' || host === '::'
		const category = DSH_CORE_PORT_SET.has(port)
			? 'core'
			: (port >= 3000 && port <= 9999
				? 'dev'
				: (port >= 49152 ? 'ephemeral' : 'service'))

		if (!map.has(port)) {
			map.set(port, {
				port,
				command,
				pid: Number.isNaN(pid) ? null : pid,
				host,
				isWildcard,
				category
			})
		} else {
			const existing = map.get(port)
			if (isWildcard && !existing.isWildcard) {
				existing.isWildcard = true
				existing.host = host
			}
		}
	}

	return Array.from(map.values()).sort((a, b) => a.port - b.port)
}

