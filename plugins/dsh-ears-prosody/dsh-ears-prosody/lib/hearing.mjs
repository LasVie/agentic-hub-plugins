/**
 * 声学层：从波形里读出「怎么说的」，**不做任何转写**。
 *
 * 这是路线 C 的地基。日常的语音转文字丢掉了说话方式——语速、停顿结构、
 * 音高起伏、句尾走向、力度变化——而这些恰恰是"我在听你说话"和"我读了一段
 * 文字"的区别。这些量全部可以从波形直接算出来，不需要模型、不需要联网、
 * 不需要密钥。
 *
 * 纪律：
 *  · 只报告测到的数字与由数字推得的**低置信**印象，绝不编造内容；
 *  · 正面/负面情绪（valence）不从声学硬猜 —— 明确写进 uncertainty；
 *  · 语料是"某人说话"，检测不到人声就直说是静音/音乐/噪声，不假装听见了。
 */
/**
 * Modified 2026-10-22 for the Agentic Hub port of dsh-ears-prosody.
 * Original source: chaoge762/dsh-ears-prosody@f28cd16bc5646fb17c3c76564598e2c37e997d77.
 * Copyright (c) 2026 chaoge888. MIT license: ../licenses/dsh-ears-prosody/LICENSE.
 * Changes: bounded anti-alias resampling, normalized pitch correlation, correct
 * segment identity, English measurements, and an activity-only contract. Removed
 * inferred speech/content/emotion/arousal/intent and subjective delivery labels.
 * The preceding original header is preserved as history; no impressions are emitted.
 */
import { AudioError, LIMITS } from './wav.mjs'

const FRAME_MS = 25
const HOP_MS = 10
const MIN_SEG_MS = 100
const MERGE_GAP_MS = 120
const F0_MIN_HZ = 70
const F0_MAX_HZ = 400
const SILENCE_DB = -58
const DIGITAL_SILENCE_DB = -100
export const ANALYSIS_SAMPLE_RATE = 8000
const clamp = (v, a, b) => Math.max(a, Math.min(b, v))
const round = (v, d = 3) => v === null || !Number.isFinite(v) ? null : Number(v.toFixed(d))
const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null
const std = (a) => {
  if (a.length < 2) return null
  const m = mean(a)
  return Math.sqrt(a.reduce((sum, v) => sum + (v - m) ** 2, 0) / (a.length - 1))
}
const percentile = (sorted, p) => sorted.length ? sorted[clamp(Math.round((sorted.length - 1) * p), 0, sorted.length - 1)] : null
const dbfs = (rms) => 20 * Math.log10(Math.max(rms, 1e-9))

/** 64-tap, 128-phase Hann-windowed sinc low-pass before resampling to 8 kHz.
 * Passband cutoff is 3.6 kHz. This bounds pitch cost without naive decimation's
 * aliasing. Edge samples are extended; sub-millisecond timing is not promised. */
export function resampleForAnalysis(samples, sampleRate) {
  if (sampleRate === ANALYSIS_SAMPLE_RATE) return samples
  const output = new Float32Array(Math.floor(samples.length * ANALYSIS_SAMPLE_RATE / sampleRate))
  const cutoff = 0.45 * ANALYSIS_SAMPLE_RATE / sampleRate
  const phases = 128
  const bank = []
  for (let phase = 0; phase < phases; phase++) {
    const kernel = new Float64Array(64)
    let sum = 0
    for (let k = 0; k < 64; k++) {
      const distance = k - 31 - phase / phases
      const x = 2 * cutoff * distance
      const sinc = Math.abs(x) < 1e-12 ? 1 : Math.sin(Math.PI * x) / (Math.PI * x)
      const window = Math.abs(distance) >= 32 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * distance / 32)
      kernel[k] = 2 * cutoff * sinc * window
      sum += kernel[k]
    }
    for (let k = 0; k < 64; k++) kernel[k] /= sum
    bank.push(kernel)
  }
  for (let i = 0; i < output.length; i++) {
    const position = i * sampleRate / ANALYSIS_SAMPLE_RATE
    const base = Math.floor(position)
    const kernel = bank[Math.min(phases - 1, Math.floor((position - base) * phases))]
    let value = 0
    for (let k = 0; k < 64; k++) value += samples[clamp(base + k - 31, 0, samples.length - 1)] * kernel[k]
    output[i] = value
  }
  return output
}

/** Normalized autocorrelation of a DC-centered 40 ms frame, with interpolation.
 * First sufficiently strong periodic peak avoids choosing a multiple of a period.
 * An earlier strong peak rejects readily detectable fundamentals above 400 Hz. */
function estimateF0(frame, sampleRate) {
  const n = frame.length
  const centered = new Float64Array(n)
  const average = mean(frame)
  let energy = 0
  for (let i = 0; i < n; i++) { centered[i] = frame[i] - average; energy += centered[i] ** 2 }
  if (energy < 1e-8) return null
  const minLag = Math.ceil(sampleRate / F0_MAX_HZ)
  const maxLag = Math.floor(sampleRate / F0_MIN_HZ)
  const scores = new Float64Array(maxLag + 2)
  for (let lag = 2; lag <= maxLag + 1; lag++) {
    let sum = 0
    let leftEnergy = 0
    let rightEnergy = 0
    for (let i = 0; i < n - lag; i++) {
      const left = centered[i]
      const right = centered[i + lag]
      sum += left * right
      leftEnergy += left * left
      rightEnergy += right * right
    }
    scores[lag] = sum / (Math.sqrt(leftEnergy * rightEnergy) || 1)
  }
  let best = 0
  const peaks = []
  for (let lag = minLag; lag <= maxLag; lag++) {
    if (scores[lag] >= scores[lag - 1] && scores[lag] > scores[lag + 1]) {
      peaks.push(lag)
      best = Math.max(best, scores[lag])
    }
  }
  if (best < 0.7) return null
  for (let lag = 3; lag < minLag; lag++) {
    if (scores[lag] >= scores[lag - 1] && scores[lag] > scores[lag + 1] && scores[lag] >= Math.max(0.7, 0.9 * best)) return null
  }
  const lag = peaks.find((candidate) => scores[candidate] >= Math.max(0.7, best * 0.9))
  const denominator = 2 * (2 * scores[lag] - scores[lag - 1] - scores[lag + 1])
  const shift = denominator ? (scores[lag + 1] - scores[lag - 1]) / denominator : 0
  const refined = lag + (Math.abs(shift) <= 1 ? shift : 0)
  const f0 = sampleRate / refined
  return f0 >= F0_MIN_HZ - 0.25 && f0 <= F0_MAX_HZ + 0.25 ? clamp(f0, F0_MIN_HZ, F0_MAX_HZ) : null
}

function slope(points) {
  if (points.length < 6) return null
  const mx = mean(points.map((p) => p.t))
  const my = mean(points.map((p) => p.value))
  let numerator = 0
  let denominator = 0
  for (const p of points) { numerator += (p.t - mx) * (p.value - my); denominator += (p.t - mx) ** 2 }
  return denominator ? numerator / denominator : null
}
const contourLabel = (value) => value === null ? 'insufficient_data' : value > 8 ? 'rising' : value < -8 ? 'falling' : 'steady'

/** Analyze observable acoustic activity. It is not a speech detector. */
export function analyze(input, inputRate) {
  if (!(input instanceof Float32Array) || !Number.isInteger(inputRate) || inputRate < LIMITS.minSampleRate || inputRate > LIMITS.maxSampleRate) throw new AudioError('INVALID_AUDIO', '输入必须是采样率为 8000–48000 Hz、已归一化的单声道 Float32 音频。')
  if (input.length / inputRate < LIMITS.minSeconds || input.length / inputRate > LIMITS.maxSeconds) throw new AudioError('INVALID_AUDIO', '分析音频的时长必须在 0.1–60 秒之间。')
  for (const sample of input) if (!Number.isFinite(sample) || Math.abs(sample) > 1) throw new AudioError('INVALID_SAMPLE', '输入采样值必须为有限数值，并归一化到 -1 至 1 的范围内。')
  const samples = resampleForAnalysis(input, inputRate)
  const sampleRate = ANALYSIS_SAMPLE_RATE
  const frameLen = Math.round(sampleRate * FRAME_MS / 1000)
  const pitchLen = Math.round(sampleRate * 0.04)
  const hop = Math.round(sampleRate * HOP_MS / 1000)
  const frameCount = 1 + Math.floor((samples.length - frameLen) / hop)
  const durationSec = input.length / inputRate
  const db = new Float64Array(frameCount)
  const zcr = new Float64Array(frameCount)
  let wholeEnergy = 0
  for (const sample of samples) wholeEnergy += sample * sample
  for (let f = 0; f < frameCount; f++) {
    const start = f * hop
    let sum = 0
    let crossings = 0
    let prevNeg = samples[start] < 0
    for (let i = 0; i < frameLen; i++) {
      const sample = samples[start + i]
      sum += sample * sample
      const neg = sample < 0
      if (neg !== prevNeg) crossings++
      prevNeg = neg
    }
    db[f] = dbfs(Math.sqrt(sum / frameLen))
    zcr[f] = crossings / frameLen
  }
  const sortedDb = Float64Array.from(db).sort()
  const peakDb = sortedDb[sortedDb.length - 1]
  const referenceDb = percentile(sortedDb, 0.95)
  const roughGateDb = Math.max(referenceDb - 18, SILENCE_DB + 6)
  // Known digital silence is stronger floor evidence than a quiet tonal passage.
  // Excluding it would misclassify a second, softer level as background noise.
  const digitalSilence = sortedDb.filter((v) => v <= DIGITAL_SILENCE_DB)
  const belowGate = sortedDb.filter((v) => v > DIGITAL_SILENCE_DB && v <= roughGateDb)
  const noiseFloorDb = digitalSilence.length >= 8 ? percentile(digitalSilence, 0.9)
    : belowGate.length >= 8 ? percentile(belowGate, 0.9) : null
  const thresholdDb = referenceDb <= SILENCE_DB ? SILENCE_DB : noiseFloorDb === null
    ? Math.max(referenceDb - 25, SILENCE_DB)
    : Math.max(SILENCE_DB, Math.min(noiseFloorDb + 8, referenceDb - 25))

  // Preserve the upstream energy-gate / merge approach, without claiming speech.
  const merged = []
  for (let f = 0; f < frameCount; f++) {
    if (db[f] <= thresholdDb) continue
    const last = merged[merged.length - 1]
    if (last && (f - last[1] - 1) * HOP_MS < MERGE_GAP_MS) last[1] = f
    else merged.push([f, f])
  }
  const segments = merged.filter(([a, b]) => (b - a + 1) * HOP_MS >= MIN_SEG_MS)
  const intervals = segments.map(([a, b], index) => ({ index: index + 1,
    startSec: round(a * hop / sampleRate), endSec: round(Math.min(durationSec, (b * hop + frameLen) / sampleRate)),
    durationMs: round(((b - a) * hop + frameLen) / sampleRate * 1000) }))
  const activeSec = intervals.reduce((sum, interval) => sum + interval.durationMs / 1000, 0)
  const pauses = intervals.slice(1).map((interval, i) => Math.max(0, (interval.startSec - intervals[i].endSec) * 1000))
  const limitations = [
    '基于能量检测到的活动并不代表已确认的人类语音；音乐、噪声及其他声音也可能被检测为活动。',
    '自适应能量门限可能遗漏很轻的声音；能量范围描述的是检测到的活动，并非经过校准的响度测量。',
    '音高采用自相关方法近似估计，范围限于 70–400 Hz；噪声较大或多声部音频可能无法可靠估计。',
    '每秒活动时长内的能量峰数量仅作为节奏代理指标，并非每秒音节数或词数。',
    '本工具不进行转写，也不推断说话者身份、情绪、唤醒程度、意图或临床状况。',
    '双声道会取平均值合成为单声道；反相声道可能相互抵消。分析采用 8 kHz 单声道信号，帧时间为近似值。',
  ]
  if (durationSec < 1.5) limitations.push('短于 1.5 秒的音频不足以充分评估停顿和节奏。')
  if (!segments.length) limitations.push('没有持续的声学活动超过能量门限；无法提供音高和节奏指标。')

  const f0Series = []
  segments.forEach(([a, b], index) => {
    for (let f = a; f <= b; f++) {
      if (zcr[f] > 0.3 || db[f] <= thresholdDb) continue
      const start = Math.min(f * hop, samples.length - pitchLen)
      const f0 = estimateF0(samples.subarray(start, start + pitchLen), sampleRate)
      if (f0 !== null) f0Series.push({ t: (start + pitchLen / 2) / sampleRate, value: f0, segment: index })
    }
  })
  const values = f0Series.map((p) => p.value)
  const sortedPitch = [...values].sort((a, b) => a - b)
  if (values.length < 10) limitations.push('可测得的周期性帧不足 10 个；音高统计和轮廓的依据有限。')
  const contours = intervals.map((interval, index) => {
    const value = slope(f0Series.filter((p) => p.segment === index))
    return { index: interval.index, startSec: interval.startSec, endSec: interval.endSec,
      slopeHzPerSec: round(value, 1), contour: contourLabel(value) }
  })
  const lastIndex = segments.length - 1
  const lastPoints = f0Series.filter((p) => p.segment === lastIndex)
  let endingPitch = 'insufficient_data'
  if (lastPoints.length >= 6) {
    const half = Math.floor(lastPoints.length / 2)
    const delta = mean(lastPoints.slice(half).map((p) => p.value)) - mean(lastPoints.slice(0, half).map((p) => p.value))
    endingPitch = delta > 6 ? 'rising' : delta < -6 ? 'falling' : 'steady'
  }
  const activeDb = []
  const inActivity = new Uint8Array(frameCount)
  for (const [a, b] of segments) for (let f = a; f <= b; f++) { activeDb.push(db[f]); inActivity[f] = 1 }
  activeDb.sort((a, b) => a - b)
  const rangeDb = activeDb.length ? percentile(activeDb, 0.95) - percentile(activeDb, 0.1) : null
  const lastSegment = segments[lastIndex]
  const tail = []
  if (lastSegment) for (let f = Math.max(lastSegment[0], lastSegment[1] - 29); f <= lastSegment[1]; f++) tail.push({ t: f * HOP_MS / 1000, value: db[f] })
  const endingSlope = slope(tail)

  // Require at least 1 dB prominence on both sides: a flat tone is not pacing.
  const smooth = new Float64Array(frameCount)
  for (let f = 0; f < frameCount; f++) {
    const a = Math.max(0, f - 1)
    const b = Math.min(frameCount - 1, f + 1)
    let sum = 0
    for (let i = a; i <= b; i++) sum += db[i]
    smooth[f] = sum / (b - a + 1)
  }
  let peaks = 0
  let lastPeak = -Infinity
  for (let f = 1; f < frameCount - 1; f++) {
    if (!inActivity[f] || smooth[f] < thresholdDb + 3 || (f - lastPeak) * HOP_MS < 80) continue
    if (!(smooth[f] > smooth[f - 1] && smooth[f] >= smooth[f + 1])) continue
    let leftMin = smooth[f]
    let rightMin = smooth[f]
    for (let i = Math.max(0, f - 10); i < f; i++) leftMin = Math.min(leftMin, smooth[i])
    for (let i = f + 1; i <= Math.min(frameCount - 1, f + 10); i++) rightMin = Math.min(rightMin, smooth[i])
    if (smooth[f] - Math.max(leftMin, rightMin) < 1) continue
    peaks++
    lastPeak = f
  }
  return {
    activity: { segmentCount: intervals.length, activeSec: round(activeSec), activeRatio: round(activeSec / durationSec), segments: intervals },
    pause: { count: pauses.length, durationsMs: pauses.map((p) => Math.round(p)), longestMs: pauses.length ? Math.round(Math.max(...pauses)) : 0,
      meanMs: pauses.length ? Math.round(mean(pauses)) : 0, leadingSilenceMs: Math.round((intervals[0]?.startSec ?? durationSec) * 1000),
      trailingSilenceMs: intervals.length ? Math.round((durationSec - intervals[intervals.length - 1].endSec) * 1000) : 0 },
    pitch: { meanHz: round(mean(values), 1), stdHz: round(std(values), 1), p10Hz: round(percentile(sortedPitch, 0.1), 1), p90Hz: round(percentile(sortedPitch, 0.9), 1),
      voicedFrames: values.length, contours, ending: endingPitch },
    energy: { thresholdDb: round(thresholdDb, 1), noiseFloorDb: round(noiseFloorDb, 1), rangeDb: round(rangeDb, 1), peakDb: round(peakDb, 1),
      rmsDb: round(dbfs(Math.sqrt(wholeEnergy / samples.length)), 1), endingSlopeDbPerSec: round(endingSlope, 1),
      ending: endingSlope === null ? 'insufficient_data' : endingSlope < -10 ? 'decreasing' : endingSlope > 8 ? 'increasing' : 'steady',
      measurement: '分析用单声道信号的均方根电平，单位为 dBFS；peakDb 是 25 毫秒帧的最大均方根电平。' },
    tempo: { energyPeaks: peaks, peaksPerActiveSecond: activeSec > 0.3 ? round(peaks / activeSec, 2) : null,
      definition: '对平滑后的均方根包络中至少突出 1 dB 的峰计数，再除以活动时长；这不是音节速率或词速。' },
    limitations,
  }
}
