"use strict";

const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const path = require("node:path");
const {test} = require("node:test");

const payload = process.env.SCORE_TEST_PAYLOAD || path.join(__dirname, "../offline-score-workbench");
const engine = require(path.join(payload, "web/vendor/verovio-toolkit-wasm.js"));
const xml = readFileSync(path.join(payload, "web/example.musicxml"), "utf8");
const mei = readFileSync(path.join(__dirname, "fixtures/双音符.mei"), "utf8");
const ready = new Promise(resolve => {
  if (engine.module.calledRun) resolve();
  else engine.module.onRuntimeInitialized = resolve;
});

function decodeMidi(base64) {
  const bytes = Buffer.from(base64, "base64");
  assert.equal(bytes.toString("ascii", 0, 4), "MThd");
  assert.equal(bytes.readUInt32BE(4), 6);
  const division = bytes.readUInt16BE(12);
  const notes = [];
  let offset = 14;
  for (let track = 0; track < bytes.readUInt16BE(10); track++) {
    assert.equal(bytes.toString("ascii", offset, offset + 4), "MTrk");
    const end = offset + 8 + bytes.readUInt32BE(offset + 4);
    offset += 8;
    let tick = 0;
    let runningStatus;
    const sounding = new Map();
    function variableLength() {
      let value = 0;
      let byte;
      do {
        assert.ok(offset < end);
        byte = bytes[offset++];
        value = (value << 7) | (byte & 127);
      } while (byte & 128);
      return value;
    }
    while (offset < end) {
      tick += variableLength();
      let status = bytes[offset++];
      if (status < 128) {
        offset--;
        status = runningStatus;
      }
      if (status === 255) {
        offset++;
        const length = variableLength();
        offset += length;
        continue;
      }
      assert.ok(status >= 128 && status < 240);
      runningStatus = status;
      const type = status & 240;
      const pitch = bytes[offset++];
      if (type === 192 || type === 208) continue;
      const velocity = bytes[offset++];
      const key = (status & 15) + ":" + pitch;
      if (type === 144 && velocity > 0) {
        assert.ok(!sounding.has(key));
        sounding.set(key, tick);
      } else if (type === 128 || type === 144) {
        const start = sounding.get(key);
        assert.ok(start !== undefined);
        notes.push({track, pitch, start: start / division, length: (tick - start) / division, tickLength: 1 / division});
        sounding.delete(key);
      }
    }
    assert.equal(offset, end);
    assert.equal(sounding.size, 0);
  }
  assert.equal(offset, bytes.length);
  return notes;
}

async function render(input) {
  await ready;
  const score = new engine.toolkit();
  try {
    assert.match(score.getVersion(), /^6\.4\.0/);
    score.setOptions({
      svgViewBox: true, adjustPageHeight: true, pageWidth: 1600, pageHeight: 1600,
      footer: "none", fontTextLiberation: false, smuflTextFont: "none",
    });
    assert.ok(score.loadData(input));
    const count = score.getPageCount();
    const pages = Array.from({length: count}, (_, index) => score.renderToSVG(index + 1));
    const notes = decodeMidi(score.renderToMIDI());
    return {pages, notes, first: score.getMIDIValuesForElement(input === mei ? "mei-first" : "melody-one")};
  } finally {
    score.destroy();
  }
}

function notationBeats(note) {
  // Verovio ends the exported note one MIDI tick before the notated boundary.
  return [note.pitch, note.start, note.length + note.tickLength];
}

test("MusicXML engraves two parts and encodes rests, F-sharp and a tie in MIDI", async () => {
  const {pages, notes, first} = await render(xml);
  assert.equal(pages.length, 1);
  for (const fragment of ["晨光练习曲", 'class="staff"', 'class="rest"', 'class="accid"', 'class="tie"']) {
    assert.ok(pages[0].includes(fragment), fragment);
  }
  assert.deepEqual(first, {pitch: 60, time: 0, duration: 500});
  const melody = notes.filter(note => note.track === 1).map(notationBeats);
  assert.deepEqual(melody, [[60, 0, 1], [66, 2, 1], [67, 3, 2], [64, 5, 1]]);
  assert.deepEqual(notes.filter(note => note.track === 2).map(note => note.pitch), [48, 43]);
});

test("editing only the first pitch changes only the corresponding MIDI note", async () => {
  const original = await render(xml);
  const edited = await render(xml.replace("<step>C</step>", "<step>D</step>"));
  assert.notEqual(original.pages[0], edited.pages[0]);
  assert.deepEqual(edited.first, {pitch: 62, time: 0, duration: 500});
  const expected = original.notes.map((note, index) => index === 0 ? {...note, pitch: 62} : note);
  assert.deepEqual(edited.notes, expected);
});

test("MEI fixture engraves and yields two half notes", async () => {
  const {pages, notes, first} = await render(mei);
  assert.equal(pages.length, 1);
  assert.match(pages[0], /mei-first/);
  assert.equal(first.pitch, 60);
  assert.deepEqual(notes.map(notationBeats), [[60, 0, 2], [62, 2, 2]]);
});

test("longer bounded MusicXML produces multiple pages with actual note glyphs", async () => {
  const start = xml.indexOf('  <part id="P1">');
  const end = xml.indexOf('  <part id="P2">');
  const firstPart = xml.slice(start, end).replace(/<measure number="2">[\s\S]*?<\/measure>/, "")
    .replace('<tie type="start"/>', "").replace('<notations><tied type="start"/></notations>', "");
  const repeated = Array.from({length: 59}, (_, index) =>
    '<measure number="' + (index + 2) + '"><note><pitch><step>G</step><octave>4</octave></pitch>' +
    '<duration>4</duration><type>whole</type></note></measure>').join("\n");
  const longer = xml.slice(0, start).replace(/    <score-part id="P2">.*\n/, "") +
    firstPart.replace("</part>", repeated + "</part>") + "</score-partwise>";
  const {pages} = await render(longer);
  assert.ok(pages.length > 1 && pages.length <= 16);
  assert.ok(pages.every(page => page.includes('class="note"')));
});
