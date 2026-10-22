#!/usr/bin/env node
/** Local-only entry point for dsh-ears-prosody 1.0.1. No packages or network calls. */
import { constants, openSync, fstatSync, readSync, closeSync } from 'node:fs'
import { isAbsolute } from 'node:path'
import { AudioError, LIMITS, decodeWav } from '../lib/wav.mjs'
import { analyze, ANALYSIS_SAMPLE_RATE } from '../lib/hearing.mjs'

const VERSION = '1.0.1'

function readLocalWav(path) {
  if (!isAbsolute(path) || path.includes('\0')) throw new AudioError('INVALID_PATH', '请提供一个本地 WAV 文件的绝对路径。')
  let fd
  try {
    // Nonblocking open prevents FIFOs/devices from waiting before fstat rejects them.
    // Refuse symlinks so this local-file interface has no implicit indirection.
    fd = openSync(path, constants.O_RDONLY | constants.O_NONBLOCK | (constants.O_NOFOLLOW || 0))
    const before = fstatSync(fd)
    if (!before.isFile()) throw new AudioError('INVALID_PATH', '输入必须是普通文件，不能是目录、设备或管道。')
    if (before.size > LIMITS.maxBytes) throw new AudioError('FILE_TOO_LARGE', 'WAV 文件大小超过 12 MiB。')
    if (before.size < 44) throw new AudioError('INVALID_WAV', '文件过短，无法包含完整的 WAV 文件头。')
    const bytes = Buffer.alloc(before.size)
    let offset = 0
    while (offset < bytes.length) {
      const count = readSync(fd, bytes, offset, bytes.length - offset, offset)
      if (!count) throw new AudioError('FILE_CHANGED', '读取过程中输入文件发生变化；请使用保持不变的文件重试。')
      offset += count
    }
    const extra = Buffer.alloc(1)
    const after = fstatSync(fd)
    if (readSync(fd, extra, 0, 1, offset) !== 0 || after.size !== before.size || after.mtimeMs !== before.mtimeMs) throw new AudioError('FILE_CHANGED', '读取过程中输入文件发生变化；请使用保持不变的文件重试。')
    return bytes
  } finally { if (fd !== undefined) closeSync(fd) }
}

try {
  if (Number(process.versions.node.split('.')[0]) < 20) throw new AudioError('NODE_VERSION', '需要 Node.js 20 或更高版本。')
  if (process.argv.length !== 3) throw new AudioError('INVALID_ARGUMENT', '用法：node scripts/analyze.mjs /绝对路径/录音.wav')
  const decoded = decodeWav(readLocalWav(process.argv[2]))
  const { samples, ...audio } = decoded
  const result = analyze(samples, decoded.sampleRate)
  process.stdout.write(JSON.stringify({ ok: true, version: VERSION, audio: { ...audio, analysisSampleRate: ANALYSIS_SAMPLE_RATE }, ...result }) + '\n')
} catch (error) {
  let code = error instanceof AudioError ? error.code : 'READ_FAILED'
  let message = error instanceof AudioError ? error.message : '无法读取本地 WAV 文件。'
  if (error.code === 'ENOENT') { code = 'FILE_NOT_FOUND'; message = '输入文件不存在。' }
  else if (error.code === 'ELOOP') { code = 'INVALID_PATH'; message = '不接受符号链接；请提供普通文件的实际路径。' }
  else if (error.code === 'EACCES' || error.code === 'EPERM') { code = 'ACCESS_DENIED'; message = '无法读取输入文件，请检查访问权限。' }
  process.stdout.write(JSON.stringify({ ok: false, version: VERSION, error: { code, message } }) + '\n')
  process.exitCode = 1
}
