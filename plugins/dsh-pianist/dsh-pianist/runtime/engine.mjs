// WorkSwarm port. Upstream MIT sources and notices are bundled in vendor/ and licenses/.

// plugins/dsh-pianist/dsh-pianist/vendor/core/errors.ts
var ScoreValidationError = class extends Error {
  issues;
  constructor(issues) {
    super(`Invalid score: ${issues.join("; ")}`);
    this.name = "ScoreValidationError";
    this.issues = [...issues];
  }
};
var ScoreParseError = class extends Error {
  constructor(message) {
    super(message);
    this.name = "ScoreParseError";
  }
};

// plugins/dsh-pianist/dsh-pianist/vendor/core/normalizer.ts
function record(value, path) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ScoreParseError(`${path} must be an object`);
  }
  return value;
}
function array(value, path) {
  if (!Array.isArray(value)) {
    throw new ScoreParseError(`${path} must be an array`);
  }
  return value;
}
function toBigInt(value, path) {
  if (typeof value === "bigint") {
    return value;
  }
  if (typeof value === "number" && Number.isInteger(value)) {
    return BigInt(value);
  }
  if (typeof value === "string" && /^-?\d+$/.test(value)) {
    return BigInt(value);
  }
  throw new ScoreParseError(`${path} must be an integer tick (number or string)`);
}
function toNumber(value, path) {
  const number = typeof value === "number" ? value : Number(value);
  if (Number.isFinite(number) === false) {
    throw new ScoreParseError(`${path} must be a finite number`);
  }
  return number;
}
function normalizeTickFields(input, path) {
  const event = record(input, path);
  const result = { ...event };
  const type = result.type;
  const requireField = (field) => {
    if (field in result) {
      return;
    }
    throw new ScoreParseError(`${path}.${field} is required`);
  };
  if (type === "note" || type === "rest") {
    requireField("startTick");
    requireField("durationTicks");
  } else if (type === "chord") {
    requireField("startTick");
  } else if (type === "pedal") {
    requireField("startTick");
    requireField("endTick");
  } else if (type === "tuplet") {
    requireField("actual");
    requireField("normal");
    requireField("startTick");
    requireField("durationTicks");
  }
  if ("startTick" in result) {
    result.startTick = toBigInt(result.startTick, `${path}.startTick`);
  }
  if ("durationTicks" in result) {
    result.durationTicks = toBigInt(result.durationTicks, `${path}.durationTicks`);
  }
  if ("endTick" in result) {
    result.endTick = toBigInt(result.endTick, `${path}.endTick`);
  }
  if ("tick" in result) {
    result.tick = toBigInt(result.tick, `${path}.tick`);
  }
  if ("notes" in result) {
    result.notes = array(result.notes, `${path}.notes`).map((note, index) => {
      const obj = record(note, `${path}.notes[${index}]`);
      const normalized = { ...obj };
      if ("durationTicks" in obj === false) {
        throw new ScoreParseError(`${path}.notes[${index}].durationTicks is required`);
      }
      normalized.durationTicks = toBigInt(obj.durationTicks, `${path}.notes[${index}].durationTicks`);
      return normalized;
    });
  }
  if ("events" in result) {
    result.events = array(result.events, `${path}.events`).map(
      (child, index) => normalizeTickFields(child, `${path}.events[${index}]`)
    );
  }
  return result;
}
function normalizeScore(input) {
  if (typeof input !== "object" || input === null || Array.isArray(input)) {
    throw new ScoreParseError("Score must be an object");
  }
  const raw = record(input, "Score");
  const tempoMap = array(raw.tempoMap, "tempoMap");
  const timeSignatureMap = raw.timeSignatureMap === void 0 ? [] : array(raw.timeSignatureMap, "timeSignatureMap");
  const tracks = array(raw.tracks, "tracks");
  const score = {
    ...raw,
    ppq: toNumber(raw.ppq, "ppq"),
    tempoMap: tempoMap.map((event, index) => {
      const obj = record(event, `tempoMap[${index}]`);
      return {
        ...obj,
        tick: toBigInt(obj.tick, `tempoMap[${index}].tick`),
        bpm: toNumber(obj.bpm, `tempoMap[${index}].bpm`)
      };
    }),
    timeSignatureMap: timeSignatureMap.map((event, index) => {
      const obj = record(event, `timeSignatureMap[${index}]`);
      return {
        ...obj,
        tick: toBigInt(obj.tick, `timeSignatureMap[${index}].tick`),
        numerator: toNumber(obj.numerator, `timeSignatureMap[${index}].numerator`),
        denominator: toNumber(obj.denominator, `timeSignatureMap[${index}].denominator`)
      };
    }),
    tracks: tracks.map((track, trackIndex) => {
      const trackObj = record(track, `tracks[${trackIndex}]`);
      const voices = array(trackObj.voices, `tracks[${trackIndex}].voices`);
      return {
        ...trackObj,
        voices: voices.map((voice, voiceIndex) => {
          const voiceObj = record(voice, `tracks[${trackIndex}].voices[${voiceIndex}]`);
          const events = array(voiceObj.events, `tracks[${trackIndex}].voices[${voiceIndex}].events`);
          return {
            ...voiceObj,
            events: events.map(
              (event, eventIndex) => normalizeTickFields(event, `tracks[${trackIndex}].voices[${voiceIndex}].events[${eventIndex}]`)
            )
          };
        })
      };
    })
  };
  return score;
}

// plugins/dsh-pianist/dsh-pianist/vendor/core/tempo-map.ts
var TempoMap = class _TempoMap {
  ppq;
  events;
  constructor(ppq, events) {
    if (Number.isInteger(ppq) === false || ppq <= 0) {
      throw new Error("PPQ must be a positive integer");
    }
    if (events.length === 0) {
      throw new Error("TempoMap requires at least one tempo event");
    }
    this.ppq = ppq;
    this.events = [...events].map((event) => ({ tick: BigInt(event.tick), bpm: Number(event.bpm) })).sort((a, b) => a.tick < b.tick ? -1 : a.tick > b.tick ? 1 : 0);
  }
  static default(ppq, bpm = 120) {
    return new _TempoMap(ppq, [{ tick: 0n, bpm }]);
  }
  bpmAt(tick) {
    const target = BigInt(tick);
    let bpm = this.events[0].bpm;
    for (const event of this.events) {
      if (event.tick <= target) {
        bpm = event.bpm;
      } else {
        break;
      }
    }
    return bpm;
  }
  get segments() {
    const segments = [];
    for (let i = 0; i < this.events.length; i += 1) {
      const current = this.events[i];
      const next = this.events[i + 1];
      segments.push({
        startTick: current.tick,
        endTick: next ? next.tick : null,
        bpm: current.bpm
      });
    }
    return segments;
  }
  /** Convert an absolute tick to absolute seconds. */
  tickToSeconds(tick) {
    const target = BigInt(tick);
    let seconds = 0;
    let cursor = 0n;
    for (const segment of this.segments) {
      const start = segment.startTick;
      if (target < start) {
        break;
      }
      if (cursor < start) {
        seconds += Number(start - cursor) * 60 / this.events[0].bpm / this.ppq;
        cursor = start;
      }
      const end = segment.endTick ?? target;
      if (target <= end) {
        seconds += Number(target - cursor) * 60 / segment.bpm / this.ppq;
        return seconds;
      }
      seconds += Number(end - cursor) * 60 / segment.bpm / this.ppq;
      cursor = end;
    }
    seconds += Number(target - cursor) * 60 / this.events[this.events.length - 1].bpm / this.ppq;
    return seconds;
  }
  /** Convert absolute seconds to an approximate integer tick. */
  secondsToTick(seconds) {
    if (Number.isFinite(seconds) === false || seconds < 0) {
      throw new Error("seconds must be a finite non-negative number");
    }
    const target = seconds;
    const segments = this.segments;
    let cursorSeconds = 0;
    let cursorTick = 0n;
    for (let i = 0; i < segments.length; i += 1) {
      const segment = segments[i];
      const segmentStart = segment.startTick;
      if (cursorTick < segmentStart) {
        cursorSeconds += Number(segmentStart - cursorTick) * 60 / this.events[0].bpm / this.ppq;
        cursorTick = segmentStart;
      }
      const segmentDurationTicks = segment.endTick === null ? Number.MAX_SAFE_INTEGER : Number(segment.endTick - cursorTick);
      const segmentDurationSeconds = segmentDurationTicks * 60 / segment.bpm / this.ppq;
      if (target < cursorSeconds + segmentDurationSeconds || segment.endTick === null) {
        const ticksInSegment = (target - cursorSeconds) * segment.bpm * this.ppq / 60;
        return cursorTick + BigInt(Math.max(0, Math.round(ticksInSegment)));
      }
      cursorSeconds += segmentDurationSeconds;
      cursorTick = segment.endTick;
    }
    return cursorTick;
  }
};

// plugins/dsh-pianist/dsh-pianist/vendor/core/validator.ts
var MIN_MIDI = 21;
var MAX_MIDI = 108;
var MAX_VELOCITY = 1;
function isNonNegativeTick(value) {
  return BigInt(value) >= 0n;
}
function isPositiveTick(value) {
  return BigInt(value) > 0n;
}
function isValidId(value) {
  return typeof value === "string" && value.length > 0;
}
function validateTempoMap(tempoMap) {
  const issues = [];
  if (tempoMap.length === 0) {
    issues.push("tempoMap must not be empty");
    return issues;
  }
  for (let i = 0; i < tempoMap.length; i += 1) {
    const tempo = tempoMap[i];
    if (isNonNegativeTick(tempo.tick) === false) {
      issues.push(`tempoMap[${i}].tick must be non-negative`);
    }
    if (Number.isFinite(tempo.bpm) === false || tempo.bpm <= 0) {
      issues.push(`tempoMap[${i}].bpm must be a positive finite number`);
    }
    if (i > 0 && BigInt(tempo.tick) <= BigInt(tempoMap[i - 1].tick)) {
      issues.push(`tempoMap must be sorted by tick (index ${i})`);
    }
  }
  if (tempoMap.length > 0 && BigInt(tempoMap[0].tick) !== 0n) {
    issues.push("tempoMap[0].tick must be 0");
  }
  return issues;
}
function validateTimeSignatureMap(timeSignatureMap) {
  const issues = [];
  for (let i = 0; i < timeSignatureMap.length; i += 1) {
    const sig = timeSignatureMap[i];
    if (isNonNegativeTick(sig.tick) === false) {
      issues.push(`timeSignatureMap[${i}].tick must be non-negative`);
    }
    if (Number.isInteger(sig.numerator) === false || sig.numerator <= 0) {
      issues.push(`timeSignatureMap[${i}].numerator must be a positive integer`);
    }
    if (Number.isInteger(sig.denominator) === false || sig.denominator <= 0) {
      issues.push(`timeSignatureMap[${i}].denominator must be a positive integer`);
    }
    if (i > 0 && BigInt(sig.tick) <= BigInt(timeSignatureMap[i - 1].tick)) {
      issues.push(`timeSignatureMap must be sorted by tick (index ${i})`);
    }
  }
  return issues;
}
function validateNote(note, path, voiceId, trackId) {
  const issues = [];
  if (isValidId(note.id) === false) {
    issues.push(`${path}.id must be a non-empty string`);
  }
  if (note.type !== "note") {
    issues.push(`${path}.type must be "note"`);
  }
  if (Number.isInteger(note.midi) === false || note.midi < MIN_MIDI || note.midi > MAX_MIDI) {
    issues.push(`${path}.midi must be an integer in [${MIN_MIDI}, ${MAX_MIDI}]`);
  }
  if (isNonNegativeTick(note.startTick) === false) {
    issues.push(`${path}.startTick must be non-negative`);
  }
  if (isPositiveTick(note.durationTicks) === false) {
    issues.push(`${path}.durationTicks must be positive`);
  }
  if (Number.isFinite(note.velocity) === false || note.velocity < 0 || note.velocity > MAX_VELOCITY) {
    issues.push(`${path}.velocity must be in [0, ${MAX_VELOCITY}]`);
  }
  if (note.voiceId !== voiceId) {
    issues.push(`${path}.voiceId must match parent voice`);
  }
  if (note.trackId !== trackId) {
    issues.push(`${path}.trackId must match parent track`);
  }
  return issues;
}
function validateChord(chord, path, voiceId, trackId) {
  const issues = [];
  if (isValidId(chord.id) === false) {
    issues.push(`${path}.id must be a non-empty string`);
  }
  if (chord.type !== "chord") {
    issues.push(`${path}.type must be "chord"`);
  }
  if (isNonNegativeTick(chord.startTick) === false) {
    issues.push(`${path}.startTick must be non-negative`);
  }
  if (chord.notes.length === 0) {
    issues.push(`${path}.notes must not be empty`);
  }
  for (let i = 0; i < chord.notes.length; i += 1) {
    const note = chord.notes[i];
    if (Number.isInteger(note.midi) === false || note.midi < MIN_MIDI || note.midi > MAX_MIDI) {
      issues.push(`${path}.notes[${i}].midi must be in [${MIN_MIDI}, ${MAX_MIDI}]`);
    }
    if (isPositiveTick(note.durationTicks) === false) {
      issues.push(`${path}.notes[${i}].durationTicks must be positive`);
    }
    if (Number.isFinite(note.velocity) === false || note.velocity < 0 || note.velocity > MAX_VELOCITY) {
      issues.push(`${path}.notes[${i}].velocity must be in [0, ${MAX_VELOCITY}]`);
    }
  }
  if (chord.voiceId !== voiceId) {
    issues.push(`${path}.voiceId must match parent voice`);
  }
  if (chord.trackId !== trackId) {
    issues.push(`${path}.trackId must match parent track`);
  }
  return issues;
}
function validatePedal(pedal, path, voiceId, trackId) {
  const issues = [];
  if (isValidId(pedal.id) === false) {
    issues.push(`${path}.id must be a non-empty string`);
  }
  if (pedal.type !== "pedal") {
    issues.push(`${path}.type must be "pedal"`);
  }
  if (isNonNegativeTick(pedal.startTick) === false) {
    issues.push(`${path}.startTick must be non-negative`);
  }
  if (BigInt(pedal.endTick) <= BigInt(pedal.startTick)) {
    issues.push(`${path}.endTick must be greater than startTick`);
  }
  if (Number.isFinite(pedal.value) === false || pedal.value < 0 || pedal.value > 1) {
    issues.push(`${path}.value must be in [0, 1]`);
  }
  if (pedal.voiceId !== voiceId) {
    issues.push(`${path}.voiceId must match parent voice`);
  }
  if (pedal.trackId !== trackId) {
    issues.push(`${path}.trackId must match parent track`);
  }
  return issues;
}
function validateRest(rest, path, voiceId, trackId) {
  const issues = [];
  if (isValidId(rest.id) === false) {
    issues.push(`${path}.id must be a non-empty string`);
  }
  if (rest.type !== "rest") {
    issues.push(`${path}.type must be "rest"`);
  }
  if (isNonNegativeTick(rest.startTick) === false) {
    issues.push(`${path}.startTick must be non-negative`);
  }
  if (isPositiveTick(rest.durationTicks) === false) {
    issues.push(`${path}.durationTicks must be positive`);
  }
  if (rest.voiceId !== voiceId) {
    issues.push(`${path}.voiceId must match parent voice`);
  }
  if (rest.trackId !== trackId) {
    issues.push(`${path}.trackId must match parent track`);
  }
  return issues;
}
function extendsPastLocalContainer(endTick, container) {
  const end = BigInt(endTick);
  const containerDuration = BigInt(container.durationTicks);
  const normal = BigInt(container.normal);
  const actual = BigInt(container.actual);
  return end * normal > containerDuration * actual;
}
function validateTuplet(tuplet, path, voiceId, trackId, container) {
  const issues = [];
  if (isValidId(tuplet.id) === false) {
    issues.push(`${path}.id must be a non-empty string`);
  }
  if (tuplet.type !== "tuplet") {
    issues.push(`${path}.type must be "tuplet"`);
  }
  if (Number.isInteger(tuplet.actual) === false || tuplet.actual <= 0) {
    issues.push(`${path}.actual must be a positive integer`);
  }
  if (Number.isInteger(tuplet.normal) === false || tuplet.normal <= 0) {
    issues.push(`${path}.normal must be a positive integer`);
  }
  if (isNonNegativeTick(tuplet.startTick) === false) {
    issues.push(`${path}.startTick must be non-negative`);
  }
  if (isPositiveTick(tuplet.durationTicks) === false) {
    issues.push(`${path}.durationTicks must be positive`);
  }
  if (container !== void 0 && BigInt(tuplet.startTick) + BigInt(tuplet.durationTicks) > BigInt(container.durationTicks)) {
    issues.push(`${path} extends past its tuplet container`);
  }
  const childContainer = {
    durationTicks: tuplet.durationTicks,
    actual: tuplet.actual,
    normal: tuplet.normal
  };
  for (let i = 0; i < tuplet.events.length; i += 1) {
    const childIssues = validateMusicEvent(
      tuplet.events[i],
      `${path}.events[${i}]`,
      voiceId,
      trackId,
      childContainer
    );
    issues.push(...childIssues);
  }
  return issues;
}
function validateMusicEvent(event, path, voiceId, trackId, container) {
  if (event.type === "note") {
    const issues = validateNote(event, path, voiceId, trackId);
    if (container !== void 0 && extendsPastLocalContainer(BigInt(event.startTick) + BigInt(event.durationTicks), container)) {
      issues.push(`${path} extends past its tuplet container`);
    }
    return issues;
  }
  if (event.type === "chord") {
    const issues = validateChord(event, path, voiceId, trackId);
    if (container !== void 0) {
      for (let i = 0; i < event.notes.length; i += 1) {
        if (extendsPastLocalContainer(BigInt(event.startTick) + BigInt(event.notes[i].durationTicks), container)) {
          issues.push(`${path}.notes[${i}] extends past its tuplet container`);
        }
      }
    }
    return issues;
  }
  if (event.type === "pedal") {
    const issues = validatePedal(event, path, voiceId, trackId);
    if (container !== void 0 && extendsPastLocalContainer(event.endTick, container)) {
      issues.push(`${path} extends past its tuplet container`);
    }
    return issues;
  }
  if (event.type === "rest") {
    const issues = validateRest(event, path, voiceId, trackId);
    if (container !== void 0 && extendsPastLocalContainer(BigInt(event.startTick) + BigInt(event.durationTicks), container)) {
      issues.push(`${path} extends past its tuplet container`);
    }
    return issues;
  }
  if (event.type === "tuplet") {
    return validateTuplet(event, path, voiceId, trackId, container);
  }
  return [`${path} has unknown event type`];
}
function validateScore(score) {
  const issues = [];
  const eventIds = /* @__PURE__ */ new Set();
  const validateEventIds = (events, path) => {
    for (let index = 0; index < events.length; index += 1) {
      const event = events[index];
      const eventPath = `${path}[${index}]`;
      if (isValidId(event.id)) {
        if (eventIds.has(event.id)) {
          issues.push(`${eventPath}.id must be unique across the score`);
        }
        eventIds.add(event.id);
      }
      if (event.type === "tuplet") {
        validateEventIds(event.events, `${eventPath}.events`);
      }
    }
  };
  const derivedIds = /* @__PURE__ */ new Set();
  const checkDerivedId = (id) => {
    if (eventIds.has(id) || derivedIds.has(id)) {
      issues.push(`derived performance event id ${id} must be unique across the score`);
      return;
    }
    derivedIds.add(id);
  };
  const validateDerivedIds = (events, prefix) => {
    for (const event of events) {
      const id = `${prefix}${event.id}`;
      if (event.type === "note") {
        checkDerivedId(`${id}:on`);
        checkDerivedId(`${id}:off`);
      } else if (event.type === "chord") {
        event.notes.forEach((_, index) => {
          checkDerivedId(`${id}:${index}:on`);
          checkDerivedId(`${id}:${index}:off`);
        });
      } else if (event.type === "pedal") {
        checkDerivedId(`${id}:down`);
        checkDerivedId(`${id}:up`);
      } else if (event.type === "tuplet") {
        validateDerivedIds(event.events, `${id}:`);
      }
    }
  };
  if (isValidId(score.id) === false) {
    issues.push("score.id must be a non-empty string");
  }
  if (typeof score.title !== "string") {
    issues.push("score.title must be a string");
  }
  if (Number.isInteger(score.ppq) === false || score.ppq <= 0) {
    issues.push("score.ppq must be a positive integer");
  }
  issues.push(...validateTempoMap(score.tempoMap));
  issues.push(...validateTimeSignatureMap(score.timeSignatureMap ?? []));
  const trackIds = /* @__PURE__ */ new Set();
  const allVoiceEvents = [];
  for (let t = 0; t < score.tracks.length; t += 1) {
    const track = score.tracks[t];
    const trackPath = `tracks[${t}]`;
    if (isValidId(track.id) === false) {
      issues.push(`${trackPath}.id must be a non-empty string`);
    } else if (trackIds.has(track.id)) {
      issues.push(`${trackPath}.id must be unique`);
    }
    trackIds.add(track.id);
    if (track.instrument === void 0 || isValidId(track.instrument.id) === false) {
      issues.push(`${trackPath}.instrument.id must be a non-empty string`);
    }
    if (track.channel !== void 0 && (Number.isInteger(track.channel) === false || track.channel < 0 || track.channel > 15)) {
      issues.push(`${trackPath}.channel must be an integer in [0, 15]`);
    }
    const voiceIds = /* @__PURE__ */ new Set();
    for (let v = 0; v < track.voices.length; v += 1) {
      const voice = track.voices[v];
      const voicePath = `${trackPath}.voices[${v}]`;
      if (isValidId(voice.id) === false) {
        issues.push(`${voicePath}.id must be a non-empty string`);
      } else if (voiceIds.has(voice.id)) {
        issues.push(`${voicePath}.id must be unique within the track`);
      }
      voiceIds.add(voice.id);
      for (let e = 0; e < voice.events.length; e += 1) {
        issues.push(...validateMusicEvent(voice.events[e], `${voicePath}.events[${e}]`, voice.id, track.id));
      }
      validateEventIds(voice.events, `${voicePath}.events`);
      allVoiceEvents.push(voice.events);
    }
  }
  for (const events of allVoiceEvents) {
    validateDerivedIds(events, "");
  }
  if (issues.length > 0) {
    throw new ScoreValidationError(issues);
  }
}

// plugins/dsh-pianist/dsh-pianist/vendor/core/timeline.ts
var EVENT_TYPE_ORDER = {
  noteOff: 0,
  pedalUp: 1,
  noteOn: 2,
  pedalDown: 3,
  tempoChange: 4
};
function compareEvents(a, b) {
  if (a.tick !== b.tick) {
    return a.tick < b.tick ? -1 : 1;
  }
  const orderDiff = EVENT_TYPE_ORDER[a.type] - EVENT_TYPE_ORDER[b.type];
  if (orderDiff !== 0) {
    return orderDiff;
  }
  if (a.id < b.id) {
    return -1;
  }
  if (a.id > b.id) {
    return 1;
  }
  return 0;
}
function addNoteEvents(events, id, midi, startTick, durationTicks, velocity, tempoMap) {
  const endTick = BigInt(startTick) + BigInt(durationTicks);
  events.push({
    id: `${id}:on`,
    type: "noteOn",
    time: tempoMap.tickToSeconds(startTick),
    tick: BigInt(startTick),
    midi,
    velocity,
    noteId: id
  });
  events.push({
    id: `${id}:off`,
    type: "noteOff",
    time: tempoMap.tickToSeconds(endTick),
    tick: endTick,
    midi,
    noteId: id
  });
}
function addChordEvents(events, chord, tempoMap) {
  chord.notes.forEach((note, index) => {
    addNoteEvents(
      events,
      `${chord.id}:${index}`,
      note.midi,
      chord.startTick,
      note.durationTicks,
      note.velocity,
      tempoMap
    );
  });
}
function collectTupletScale(events, scale) {
  let result = scale;
  for (const event of events) {
    if (event.type === "tuplet") {
      result *= BigInt(event.actual);
      result = collectTupletScale(event.events, result);
    }
  }
  return result;
}
function addMusicEvent(builder, event, baseTick, scale, idPrefix) {
  if (event.type === "note") {
    const startTick = BigInt(baseTick) + BigInt(event.startTick) * scale;
    const durationTicks = BigInt(event.durationTicks) * scale;
    addNoteEvents(
      builder.events,
      `${idPrefix}${event.id}`,
      event.midi,
      startTick,
      durationTicks,
      event.velocity,
      builder.tempoMap
    );
    builder.maxTick = builder.maxTick < startTick + durationTicks ? startTick + durationTicks : builder.maxTick;
    return;
  }
  if (event.type === "chord") {
    const startTick = BigInt(baseTick) + BigInt(event.startTick) * scale;
    const shiftedChord = {
      ...event,
      id: `${idPrefix}${event.id}`,
      startTick
    };
    for (const note of event.notes) {
      const durationTicks = BigInt(note.durationTicks) * scale;
      const end = startTick + durationTicks;
      builder.maxTick = builder.maxTick < end ? end : builder.maxTick;
    }
    addChordEvents(builder.events, shiftedChord, builder.tempoMap);
    return;
  }
  if (event.type === "pedal") {
    const startTick = BigInt(baseTick) + BigInt(event.startTick) * scale;
    const endTick = BigInt(baseTick) + BigInt(event.endTick) * scale;
    builder.events.push({
      id: `${idPrefix}${event.id}:down`,
      type: "pedalDown",
      time: builder.tempoMap.tickToSeconds(startTick),
      tick: startTick,
      pedalValue: event.value
    });
    builder.events.push({
      id: `${idPrefix}${event.id}:up`,
      type: "pedalUp",
      time: builder.tempoMap.tickToSeconds(endTick),
      tick: endTick,
      pedalValue: 0
    });
    builder.maxTick = builder.maxTick < endTick ? endTick : builder.maxTick;
    return;
  }
  if (event.type === "rest") {
    const end = BigInt(baseTick) + (BigInt(event.startTick) + BigInt(event.durationTicks)) * scale;
    builder.maxTick = builder.maxTick < end ? end : builder.maxTick;
    return;
  }
  if (event.type === "tuplet") {
    addTupletEvents(builder, event, baseTick, scale, idPrefix);
    return;
  }
}
function addTupletEvents(builder, tuplet, baseTick, scale, idPrefix) {
  const containerStart = BigInt(baseTick) + BigInt(tuplet.startTick) * scale;
  const containerEnd = BigInt(baseTick) + (BigInt(tuplet.startTick) + BigInt(tuplet.durationTicks)) * scale;
  builder.maxTick = builder.maxTick < containerEnd ? containerEnd : builder.maxTick;
  const childScale = scale * BigInt(tuplet.normal) / BigInt(tuplet.actual);
  const childPrefix = `${idPrefix}${tuplet.id}:`;
  for (const event of tuplet.events) {
    addMusicEvent(builder, event, containerStart, childScale, childPrefix);
  }
}
function buildTimeline(score) {
  validateScore(score);
  const globalScale = score.tracks.reduce(
    (scale, track) => track.voices.reduce(
      (voiceScale, voice) => collectTupletScale(voice.events, voiceScale),
      scale
    ),
    1n
  );
  const timelinePPQ = score.ppq * Number(globalScale);
  const tempoMap = new TempoMap(
    timelinePPQ,
    score.tempoMap.map((event) => ({ tick: BigInt(event.tick) * globalScale, bpm: event.bpm }))
  );
  const builder = {
    events: [],
    tempoMap,
    maxTick: 0n
  };
  for (const track of score.tracks) {
    for (const voice of track.voices) {
      for (const event of voice.events) {
        addMusicEvent(builder, event, 0n, globalScale, "");
      }
    }
  }
  for (const tempo of score.tempoMap) {
    const tick = BigInt(tempo.tick) * globalScale;
    builder.events.push({
      id: `tempo:${tick}`,
      type: "tempoChange",
      time: tempoMap.tickToSeconds(tick),
      tick,
      bpm: tempo.bpm
    });
  }
  builder.events.sort(compareEvents);
  const immutableEvents = Object.freeze(builder.events.map((event) => Object.freeze({ ...event })));
  return Object.freeze({
    ppq: timelinePPQ,
    events: immutableEvents,
    durationTicks: builder.maxTick,
    durationSeconds: tempoMap.tickToSeconds(builder.maxTick)
  });
}

// plugins/dsh-pianist/dsh-pianist/vendor/core/transpose.ts
function transposeScore(score, semitones) {
  if (Number.isInteger(semitones) === false) {
    throw new Error("semitones must be an integer");
  }
  const cloned = structuredClone(score);
  transposeMusicEvents(cloned.tracks.flatMap((track) => track.voices.flatMap((voice) => voice.events)), semitones);
  validateScore(cloned);
  return cloned;
}
function transposeMusicEvents(events, semitones) {
  for (const event of events) {
    if (event.type === "note") {
      const midi = event.midi + semitones;
      if (midi < MIN_MIDI || midi > MAX_MIDI) {
        throw new ScoreValidationError([`transposed note ${event.id} is outside piano range: ${midi}`]);
      }
      event.midi = midi;
    } else if (event.type === "chord") {
      for (const note of event.notes) {
        const midi = note.midi + semitones;
        if (midi < MIN_MIDI || midi > MAX_MIDI) {
          throw new ScoreValidationError([`transposed chord note in ${event.id} is outside piano range: ${midi}`]);
        }
        note.midi = midi;
      }
    } else if (event.type === "tuplet") {
      transposeMusicEvents(event.events, semitones);
    }
  }
}

// plugins/dsh-pianist/dsh-pianist/vendor/audio/generated-piano.ts
var A4_MIDI = 69;
var A4_FREQUENCY = 440;
function midiToFrequency(midi) {
  return A4_FREQUENCY * Math.pow(2, (midi - A4_MIDI) / 12);
}
function generatePianoTone(options) {
  const { sampleRate, midi, velocity, durationSeconds } = options;
  const length = Math.max(1, Math.floor(sampleRate * durationSeconds));
  const data = new Float32Array(length);
  const baseFrequency = midiToFrequency(midi);
  const inharmonicity = 4e-4 + (midi - 21) * 1e-5;
  const brightness = 0.25 + velocity * 0.75;
  const partials = 12;
  const decaySeconds = Math.min(6, 0.8 + (108 - midi) * 0.055);
  const attackSamples = Math.max(1, Math.floor(sampleRate * 3e-3));
  const noiseAmp = 0.012 * velocity;
  for (let i = 0; i < length; i += 1) {
    const t = i / sampleRate;
    let sample = 0;
    for (let p = 1; p <= partials; p += 1) {
      const freq = baseFrequency * p * Math.sqrt(1 + inharmonicity * p * p);
      const amplitude = Math.pow(1 / p, 1.6 + (1 - brightness) * 0.7) * (1 + brightness * 0.3 * p / partials);
      sample += Math.sin(2 * Math.PI * freq * t) * amplitude;
    }
    const envelope = Math.exp(-t / decaySeconds);
    const attack = i < attackSamples ? i / attackSamples : 1;
    const noisePhase = Math.sin(2 * Math.PI * 73 * t) * Math.sin(2 * Math.PI * 157 * t + 1.3);
    const noise = noisePhase * noiseAmp * Math.exp(-t / 0.012);
    data[i] = (sample * envelope * attack + noise) * velocity;
  }
  let sum = 0;
  for (let i = 0; i < data.length; i += 1) {
    sum += data[i];
  }
  const dc = sum / data.length;
  for (let i = 0; i < data.length; i += 1) {
    data[i] -= dc;
  }
  return data;
}

// plugins/dsh-pianist/dsh-pianist/runtime/entry.ts
var text = "";
for await (const chunk of process.stdin) text += chunk;
async function main(q) {
  const notes = q.notes;
  if (!Array.isArray(notes) || notes.length < 1 || notes.length > 256) throw Error("notes \u5FC5\u987B\u5305\u542B1\u81F3256\u4E2A\u97F3\u7B26\u3002");
  const bpm = q.bpm ?? 100;
  if (!Number.isFinite(bpm) || bpm < 30 || bpm > 240) throw Error("\u901F\u5EA6\u5FC5\u987B\u4E3A30\u81F3240 BPM\u3002");
  const transpose = q.transpose ?? 0;
  if (!Number.isInteger(transpose) || Math.abs(transpose) > 24) throw Error("\u79FB\u8C03\u5FC5\u987B\u4E3A-24\u81F324\u7684\u6574\u6570\u3002");
  const events = notes.map((n, i) => {
    if (!n || !Number.isInteger(n.midi) || n.midi < 21 || n.midi > 108 || !Number.isFinite(n.start_beat) || n.start_beat < 0 || n.start_beat > 96 || !Number.isFinite(n.beats) || n.beats <= 0 || n.beats > 16 || !Number.isFinite(n.velocity ?? 0.65) || (n.velocity ?? 0.65) <= 0 || (n.velocity ?? 0.65) > 1) throw Error("\u97F3\u7B26\u9700\u8981 MIDI 21\u2013108\u3001\u975E\u8D1F start_beat\u3001\u6B63 beats \u548C0\u81F31\u7684\u529B\u5EA6\u3002");
    if (Math.round(n.beats * 960) < 1) throw Error("\u97F3\u7B26\u65F6\u503C\u8FC7\u77ED\u3002");
    return { id: `n${i}`, type: "note", midi: n.midi, startTick: Math.round(n.start_beat * 960), durationTicks: Math.round(n.beats * 960), velocity: n.velocity ?? 0.65, voiceId: "v1", trackId: "piano" };
  });
  let score = normalizeScore({ id: "piano-local", title: String(q.title ?? "\u79BB\u7EBF\u94A2\u7434\u7EC3\u4E60").slice(0, 100), ppq: 960, tempoMap: [{ tick: 0, bpm }], timeSignatureMap: [{ tick: 0, numerator: 4, denominator: 4 }], tracks: [{ id: "piano", instrument: { id: "generated-piano" }, voices: [{ id: "v1", events }] }] });
  if (transpose) score = transposeScore(score, transpose);
  const timeline = buildTimeline(score);
  const duration = timeline.durationSeconds + 0.35;
  if (duration > 60) throw Error("\u5355\u6B21\u6F14\u594F\u6700\u957F60\u79D2\uFF0C\u8BF7\u7F29\u77ED\u4E50\u8C31\u3002");
  const sampleRate = 22050;
  const mixed = new Float32Array(Math.ceil(duration * sampleRate));
  const ons = /* @__PURE__ */ new Map();
  for (const e of timeline.events) {
    if (e.type === "noteOn") ons.set(e.noteId, e);
    if (e.type === "noteOff") {
      const on = ons.get(e.noteId);
      if (!on) continue;
      const tone = generatePianoTone({ sampleRate, midi: on.midi, velocity: on.velocity, durationSeconds: e.time - on.time + 0.2 });
      const start = Math.round(on.time * sampleRate);
      const release = Math.max(1, Math.round(0.2 * sampleRate));
      for (let i = 0; i < tone.length && start + i < mixed.length; i++) {
        const fade = i >= tone.length - release ? (tone.length - i) / release : 1;
        mixed[start + i] += tone[i] * fade;
      }
    }
  }
  let peak = 0;
  for (const n of mixed) peak = Math.max(peak, Math.abs(n));
  const gain = peak > 0 ? 0.9 / Math.max(1, peak) : 1;
  const wav = Buffer.alloc(44 + mixed.length * 2);
  wav.write("RIFF", 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write("WAVEfmt ", 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(sampleRate, 24);
  wav.writeUInt32LE(sampleRate * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write("data", 36);
  wav.writeUInt32LE(mixed.length * 2, 40);
  for (let i = 0; i < mixed.length; i++) wav.writeInt16LE(Math.round(Math.max(-1, Math.min(1, mixed[i] * gain)) * 32767), 44 + i * 2);
  return { ok: true, message: "\u672C\u5730\u94A2\u7434\u97F3\u9891\u5DF2\u751F\u6210\uFF0C\u4F7F\u7528\u5408\u6210\u97F3\u8272\uFF0C\u65E0\u9700\u8D26\u53F7\u6216\u97F3\u8272\u4E0B\u8F7D\u3002", title: score.title, bpm, transpose, duration_seconds: duration, sample_rate: sampleRate, note_count: notes.length, wav_base64: wav.toString("base64"), score: JSON.parse(JSON.stringify(score, (_, v) => typeof v === "bigint" ? v.toString() : v)), timeline: JSON.parse(JSON.stringify(timeline.events, (_, v) => typeof v === "bigint" ? v.toString() : v)) };
}
try {
  process.stdout.write(JSON.stringify(await main(JSON.parse(text))));
} catch (e) {
  const msg = String(e.message);
  process.stdout.write(JSON.stringify({ ok: false, message: /[\u4e00-\u9fff]/.test(msg) ? msg : "\u4E50\u8C31\u6821\u9A8C\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u97F3\u9AD8\u8303\u56F4\u3001\u8282\u62CD\u4E0E\u79FB\u8C03\u3002" }));
}
