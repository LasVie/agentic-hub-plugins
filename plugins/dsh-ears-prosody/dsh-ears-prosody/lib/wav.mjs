/**
 * 最小 WAV 解码器 —— 只认 PCM / IEEE float，产出单声道 Float32。
 *
 * 为什么手写：这个插件的一条纪律是「能用 node 内置就不加依赖」。
 * 原生解码库（或 ffmpeg）会把这个插件变成需要构建授权的东西，
 * 而我们要它「装上就能用」。
 *
 * 支持：8/16/24/32 位整数 PCM、32/64 位浮点、WAVE_FORMAT_EXTENSIBLE 外壳、
 * 任意声道数（下混为单声道）、块按偶数字节对齐（RIFF 规范）。
 * 不认的容器（webm/opus、mp3、m4a）会抛出可读错误，由上层提示用户
 * 转成 wav，或交给「听音模型层」处理。
 */
/**
 * Modified 2026-10-22 for the Agentic Hub port of dsh-ears-prosody.
 * Original source: chaoge762/dsh-ears-prosody@f28cd16bc5646fb17c3c76564598e2c37e997d77.
 * Copyright (c) 2026 chaoge888. MIT license: ../licenses/dsh-ears-prosody/LICENSE.
 * Changes: strict bounds/format checks, finite normalized samples, explicit limits,
 * mono/stereo only, English errors, and metadata. No model-layer fallback exists.
 * The preceding original header is preserved as upstream history; these limits apply.
 */

export const LIMITS = Object.freeze({ maxBytes: 12 * 1024 * 1024, maxSeconds: 60, minSeconds: 0.1,
  minSampleRate: 8000, maxSampleRate: 48000, maxChannels: 2 })

export class AudioError extends Error {
  constructor(code, message) { super(message); this.name = 'AudioError'; this.code = code }
}
const fail = (code, message) => { throw new AudioError(code, message) }
const int24 = (bytes, o) => {
  const v = bytes[o] | (bytes[o + 1] << 8) | (bytes[o + 2] << 16)
  return (v & 0x800000) ? v - 0x1000000 : v
}

/** Decode a bounded, complete RIFF/WAVE file to an arithmetic mono mix. */
export function decodeWav(bytes) {
  if (!(bytes instanceof Uint8Array)) fail('INVALID_WAV', '输入必须是 WAV 文件字节。')
  if (bytes.byteLength > LIMITS.maxBytes) fail('FILE_TOO_LARGE', 'WAV 文件大小超过 12 MiB。')
  if (bytes.byteLength < 44) fail('INVALID_WAV', '文件过短，无法包含完整的 RIFF/WAVE 文件头。')
  const tag = (o) => String.fromCharCode(bytes[o], bytes[o + 1], bytes[o + 2], bytes[o + 3])
  if (tag(0) !== 'RIFF' || tag(8) !== 'WAVE') fail('INVALID_WAV', '仅支持小端 RIFF/WAVE 文件；请先在本地将其他格式转换为 WAV。')
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  if (view.getUint32(4, true) + 8 !== bytes.byteLength) fail('INVALID_WAV', 'RIFF 声明的大小必须与完整文件一致；不接受截断数据或多余的尾部数据。')
  let fmt = null
  let dataOffset = -1
  let dataLength = 0
  let offset = 12
  let chunks = 0
  while (offset < bytes.byteLength) {
    if (++chunks > 4096) fail('INVALID_WAV', 'WAV 文件包含过多数据块。')
    if (offset + 8 > bytes.byteLength) fail('INVALID_WAV', 'WAV 数据块头不完整。')
    const id = tag(offset)
    const size = view.getUint32(offset + 4, true)
    const body = offset + 8
    const end = body + size
    const next = end + (size % 2)
    if (end > bytes.byteLength || next > bytes.byteLength) fail('INVALID_WAV', 'WAV 数据块或其填充字节超出 RIFF 声明的范围。')
    if (id === 'fmt ') {
      if (fmt) fail('INVALID_WAV', '不接受重复的 fmt 数据块。')
      if (size < 16 || size === 17) fail('INVALID_WAV', 'fmt 数据块不完整。')
      if (size > 16 && (size < 18 || view.getUint16(body + 16, true) !== size - 18)) fail('INVALID_WAV', 'fmt 扩展长度与数据块大小不一致。')
      let audioFormat = view.getUint16(body, true)
      const channels = view.getUint16(body + 2, true)
      const sampleRate = view.getUint32(body + 4, true)
      const byteRate = view.getUint32(body + 8, true)
      const blockAlign = view.getUint16(body + 12, true)
      const bitsPerSample = view.getUint16(body + 14, true)
      if (audioFormat === 0xfffe) {
        if (size < 40 || view.getUint16(body + 16, true) < 22) fail('INVALID_WAV', 'WAVE_FORMAT_EXTENSIBLE 格式必须包含完整的扩展信息。')
        if (view.getUint16(body + 18, true) !== bitsPerSample) fail('UNSUPPORTED_WAV', '扩展格式的有效位数必须等于容器位深。')
        const guidTail = [0, 0, 16, 0, 128, 0, 0, 170, 0, 56, 155, 113]
        if (!guidTail.every((v, i) => bytes[body + 28 + i] === v)) fail('UNSUPPORTED_WAV', '不支持此 WAVE_FORMAT_EXTENSIBLE 子类型 GUID。')
        audioFormat = view.getUint32(body + 24, true)
        const mask = view.getUint32(body + 20, true)
        let maskBits = 0
        for (let m = mask; m; m >>>= 1) maskBits += m & 1
        if (mask !== 0 && maskBits !== channels) fail('INVALID_WAV', '扩展格式的声道掩码与声道数量不一致。')
      }
      if (audioFormat !== 1 && audioFormat !== 3) fail('UNSUPPORTED_WAV', '仅支持未压缩的整数 PCM 和 IEEE 浮点 WAV。')
      if (channels < 1 || channels > LIMITS.maxChannels) fail('UNSUPPORTED_WAV', '仅支持单声道和双声道 WAV 文件。')
      if (sampleRate < LIMITS.minSampleRate || sampleRate > LIMITS.maxSampleRate) fail('UNSUPPORTED_WAV', '采样率必须在 8000–48000 Hz 之间。')
      const supported = audioFormat === 1 ? [8, 16, 24, 32] : [32, 64]
      if (!supported.includes(bitsPerSample)) fail('UNSUPPORTED_WAV', '不支持此 PCM 或浮点位深。')
      const expectedAlign = channels * (bitsPerSample / 8)
      if (blockAlign !== expectedAlign || byteRate !== sampleRate * expectedAlign) fail('INVALID_WAV', 'WAV 块对齐大小或字节率与声明的格式不一致。')
      fmt = { audioFormat, channels, sampleRate, bitsPerSample, blockAlign }
    } else if (id === 'data') {
      if (dataOffset >= 0) fail('INVALID_WAV', '不接受重复的 data 数据块。')
      dataOffset = body
      dataLength = size
    }
    offset = next
  }
  if (!fmt || dataOffset < 0) fail('INVALID_WAV', '必须同时包含 fmt 和 data 数据块。')
  const { audioFormat, channels, sampleRate, bitsPerSample, blockAlign } = fmt
  if (dataLength === 0 || dataLength % blockAlign !== 0) fail('INVALID_WAV', 'WAV 数据必须包含完整且非空的采样帧。')
  const frames = dataLength / blockAlign
  const durationSec = frames / sampleRate
  if (durationSec > LIMITS.maxSeconds) fail('AUDIO_TOO_LONG', 'WAV 时长超过 60 秒。')
  if (durationSec < LIMITS.minSeconds) fail('AUDIO_TOO_SHORT', '请提供至少 100 毫秒的音频。')
  const samples = new Float32Array(frames)
  const bytesPerSample = bitsPerSample / 8
  for (let i = 0; i < frames; i++) {
    let acc = 0
    for (let c = 0; c < channels; c++) {
      const p = dataOffset + i * blockAlign + c * bytesPerSample
      let v
      if (audioFormat === 3) v = bitsPerSample === 64 ? view.getFloat64(p, true) : view.getFloat32(p, true)
      else if (bitsPerSample === 8) v = (bytes[p] - 128) / 128
      else if (bitsPerSample === 16) v = view.getInt16(p, true) / 32768
      else if (bitsPerSample === 24) v = int24(bytes, p) / 8388608
      else v = view.getInt32(p, true) / 2147483648
      if (!Number.isFinite(v) || Math.abs(v) > 1) fail('INVALID_SAMPLE', '浮点采样值必须为有限数值，并归一化到 -1 至 1 的范围内。')
      acc += v
    }
    samples[i] = acc / channels
  }
  return { sampleRate, channels, bitsPerSample, encoding: audioFormat === 1 ? 'PCM' : 'IEEE_FLOAT', durationSec, frames, samples }
}
