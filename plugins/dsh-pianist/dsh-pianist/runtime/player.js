(() => {
  // plugins/dsh-pianist/dsh-pianist/vendor/audio/generated-piano.ts
  var A4_MIDI = 69;
  var A4_FREQUENCY = 440;
  function midiToFrequency(midi) {
    return A4_FREQUENCY * Math.pow(2, (midi - A4_MIDI) / 12);
  }
  function generatePianoTone(options) {
    const { sampleRate, midi, velocity, durationSeconds } = options;
    const length = Math.max(1, Math.floor(sampleRate * durationSeconds));
    const data2 = new Float32Array(length);
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
      data2[i] = (sample * envelope * attack + noise) * velocity;
    }
    let sum = 0;
    for (let i = 0; i < data2.length; i += 1) {
      sum += data2[i];
    }
    const dc = sum / data2.length;
    for (let i = 0; i < data2.length; i += 1) {
      data2[i] -= dc;
    }
    return data2;
  }

  // plugins/dsh-pianist/dsh-pianist/runtime/player.ts
  var data = window.PIANO;
  var audio = document.querySelector("audio");
  var status = document.getElementById("status");
  var keyboard = document.getElementById("keyboard");
  var voices = /* @__PURE__ */ new Map();
  var ctx;
  var label = (n) => ["C", "C\u266F", "D", "D\u266F", "E", "F", "F\u266F", "G", "G\u266F", "A", "A\u266F", "B"][n % 12] + (Math.floor(n / 12) - 1);
  for (let n = 21; n <= 108; n++) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label(n);
    b.title = `\u6F14\u594F ${label(n)}`;
    b.dataset.midi = String(n);
    b.className = [1, 3, 6, 8, 10].includes(n % 12) ? "key black" : "key";
    b.addEventListener("click", async () => {
      ctx ??= new AudioContext();
      await ctx.resume();
      const old = voices.get(n);
      if (old) {
        old.source.stop();
        voices.delete(n);
      }
      const tone = generatePianoTone({ sampleRate: ctx.sampleRate, midi: n, velocity: 0.65, durationSeconds: 1 });
      const buffer = ctx.createBuffer(1, tone.length, ctx.sampleRate);
      buffer.copyToChannel(tone, 0);
      const source = ctx.createBufferSource();
      const gain = ctx.createGain();
      gain.gain.value = 0.35;
      source.buffer = buffer;
      source.connect(gain).connect(ctx.destination);
      voices.set(n, { source, gain });
      source.onended = () => voices.delete(n);
      source.start();
      b.classList.add("active");
      window.setTimeout(() => b.classList.remove("active"), 350);
      status.textContent = `\u6B63\u5728\u8BD5\u542C\uFF1A${label(n)} \xB7 \u672C\u5730\u5408\u6210\u97F3\u8272`;
    });
    keyboard.append(b);
  }
  function highlight() {
    const t = audio.currentTime;
    const active = /* @__PURE__ */ new Set();
    for (const e of data.timeline) {
      if (e.time > t) break;
      if (e.type === "noteOn") active.add(e.midi);
      if (e.type === "noteOff") active.delete(e.midi);
    }
    for (const b of keyboard.children) b.classList.toggle("active", active.has(Number(b.dataset.midi)));
    document.getElementById("time").textContent = `${t.toFixed(1)} / ${Number(data.duration_seconds).toFixed(1)} \u79D2`;
    if (!audio.paused) requestAnimationFrame(highlight);
  }
  document.getElementById("play").addEventListener("click", async () => {
    try {
      await audio.play();
      status.textContent = "\u6B63\u5728\u64AD\u653E \xB7 \u70B9\u51FB\u7434\u952E\u4E5F\u53EF\u8BD5\u542C";
      highlight();
    } catch {
      status.textContent = "\u64AD\u653E\u672A\u542F\u52A8\uFF0C\u8BF7\u70B9\u51FB\u97F3\u9891\u63A7\u4EF6\u91CD\u8BD5\u3002";
    }
  });
  document.getElementById("pause").addEventListener("click", () => {
    audio.pause();
    status.textContent = "\u5DF2\u6682\u505C\uFF0C\u53EF\u7EE7\u7EED\u64AD\u653E\u3002";
  });
  document.getElementById("restart").addEventListener("click", async () => {
    audio.currentTime = 0;
    await audio.play();
    status.textContent = "\u5DF2\u4ECE\u5934\u64AD\u653E";
    highlight();
  });
  audio.addEventListener("play", highlight);
  audio.addEventListener("ended", () => {
    status.textContent = "\u6F14\u594F\u7ED3\u675F\uFF0C\u53EF\u91CD\u65B0\u64AD\u653E\u6216\u8BD5\u542C\u7434\u952E\u3002";
    highlight();
  });
})();
