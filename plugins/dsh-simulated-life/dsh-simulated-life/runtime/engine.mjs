// WorkSwarm port. Upstream MIT sources and notices are bundled in vendor/ and licenses/.

// plugins/dsh-simulated-life/dsh-simulated-life/runtime/entry.ts
import { readdir as readdir2, lstat } from "node:fs/promises";
import { join as join2 } from "node:path";

// plugins/dsh-simulated-life/dsh-simulated-life/vendor/loader.ts
import { readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";
var DEFAULT_WINDOW_HOURS = 24;
async function isDirectory(path) {
  try {
    const s = await stat(path);
    return s.isDirectory();
  } catch {
    return false;
  }
}
function parseEventTime(timeStr) {
  if (typeof timeStr !== "string" || !timeStr.trim()) return NaN;
  const parsed = Date.parse(timeStr);
  return Number.isNaN(parsed) ? NaN : parsed;
}
async function loadRecentLifeEvents(workspaceDir, now = Date.now(), windowHours = DEFAULT_WINDOW_HOURS) {
  if (!workspaceDir) {
    return { events: [] };
  }
  const lifeDir = join(workspaceDir, ".life");
  if (!await isDirectory(lifeDir)) {
    return { events: [] };
  }
  let entries = [];
  try {
    entries = await readdir(lifeDir);
  } catch {
    return { events: [] };
  }
  const windowStart = now - windowHours * 3600 * 1e3;
  const windowEnd = now + 5 * 60 * 1e3;
  const loadedEvents = [];
  let latestWorldSummary;
  let latestDayDate = "";
  for (const entry of entries) {
    if (!/^\d{6}$/.test(entry)) continue;
    const dayDirPath = join(lifeDir, entry);
    if (!await isDirectory(dayDirPath)) continue;
    const eventsFilePath = join(dayDirPath, "events.json");
    let contentStr;
    try {
      contentStr = await readFile(eventsFilePath, "utf8");
    } catch {
      continue;
    }
    let dayData;
    try {
      dayData = JSON.parse(contentStr);
    } catch {
      continue;
    }
    if (!dayData || !Array.isArray(dayData.events)) {
      continue;
    }
    if (typeof dayData.world_summary === "string" && entry >= latestDayDate) {
      latestWorldSummary = dayData.world_summary;
      latestDayDate = entry;
    }
    for (const rawEvt of dayData.events) {
      if (!rawEvt || typeof rawEvt !== "object" || typeof rawEvt.id !== "string" || !rawEvt.id || typeof rawEvt.title !== "string" || !rawEvt.title || typeof rawEvt.description !== "string" || rawEvt.actors !== void 0 && (!Array.isArray(rawEvt.actors) || !rawEvt.actors.every((x) => typeof x === "string")) || rawEvt.react !== void 0 && (rawEvt.react === null || typeof rawEvt.react !== "object")) {
        continue;
      }
      const epochMs = parseEventTime(rawEvt.time);
      if (Number.isNaN(epochMs)) continue;
      if (epochMs >= windowStart && epochMs <= windowEnd) {
        loadedEvents.push({
          event: rawEvt,
          dayDate: entry,
          filePath: eventsFilePath,
          epochMs
        });
      }
    }
  }
  loadedEvents.sort((a, b) => a.epochMs - b.epochMs);
  return {
    worldSummary: latestWorldSummary,
    events: loadedEvents
  };
}

// plugins/dsh-simulated-life/dsh-simulated-life/vendor/deduplication.ts
import { createHash } from "node:crypto";
function hashEvent(event) {
  const reactKey = event.react ? `${event.react.feeling ?? ""}|${event.react.thought ?? ""}|${event.react.action ?? ""}|${event.react.updated_at ?? ""}` : "none";
  const raw = `${event.id}|${event.time}|${event.title}|${event.description}|${event.impact ?? ""}|${reactKey}`;
  return createHash("sha256").update(raw).digest("hex").slice(0, 16);
}
function evaluateDeduplication(loadedEvents, currentState, forceFull = false) {
  const previousInjected = currentState?.injectedEvents ?? {};
  const isFirstInjection = Object.keys(previousInjected).length === 0;
  if (loadedEvents.length === 0) {
    return {
      shouldInject: false,
      isFirstInjection,
      newEvents: [],
      updatedEvents: [],
      activeEvents: [],
      nextState: { injectedEvents: {}, lastInjectedTime: currentState?.lastInjectedTime ?? null }
    };
  }
  const newEvents = [];
  const updatedEvents = [];
  const nextInjectedRecords = {};
  for (const loaded of loadedEvents) {
    const evt = loaded.event;
    const currentHash = hashEvent(evt);
    const prev = previousInjected[evt.id];
    if (!prev) {
      newEvents.push(loaded);
    } else if (prev.contentHash !== currentHash) {
      updatedEvents.push(loaded);
    }
    nextInjectedRecords[evt.id] = {
      id: evt.id,
      time: evt.time,
      reactUpdatedAt: evt.react?.updated_at,
      contentHash: currentHash
    };
  }
  const hasChanges = isFirstInjection || newEvents.length > 0 || updatedEvents.length > 0 || forceFull;
  const nextState = {
    injectedEvents: nextInjectedRecords,
    lastInjectedTime: hasChanges ? Date.now() : currentState?.lastInjectedTime ?? null
  };
  return {
    shouldInject: hasChanges,
    isFirstInjection,
    newEvents,
    updatedEvents,
    activeEvents: loadedEvents,
    nextState
  };
}

// plugins/dsh-simulated-life/dsh-simulated-life/vendor/formatter.ts
function formatTimeOnly(isoTimeStr) {
  if (typeof isoTimeStr !== "string" || !isoTimeStr.trim()) return "";
  const timeMatch = isoTimeStr.match(/T(\d{2}):(\d{2})/);
  if (timeMatch) {
    return `${timeMatch[1]}:${timeMatch[2]}`;
  }
  const d = new Date(isoTimeStr);
  if (Number.isNaN(d.getTime())) return isoTimeStr;
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}
function getTypeName(type) {
  switch (type) {
    case "routine":
      return "\u65E5\u5E38\u8D77\u5C45";
    case "encounter":
      return "\u5076\u7136\u9645\u9047";
    case "accident":
      return "\u7A81\u53D1\u63D2\u66F2";
    case "work":
      return "\u5DE5\u4F5C\u63A2\u7D22";
    case "social":
      return "\u793E\u4EA4\u4EBA\u9645";
    case "fate":
      return "\u5BBF\u547D\u4E8B\u4EF6";
    default:
      return type ? String(type) : "\u751F\u6D3B\u4E8B\u4EF6";
  }
}
function formatSingleEvent(loaded) {
  const evt = loaded.event;
  const timeStr = formatTimeOnly(evt.time);
  const typeName = getTypeName(evt.type);
  const actorsStr = evt.actors && evt.actors.length > 0 ? ` (\u76F8\u5173\u4EBA\u7269: ${evt.actors.join("\u3001")})` : "";
  const locationStr = evt.location ? ` @ ${evt.location}` : "";
  let lines = [];
  lines.push(`\u2022 [${timeStr}] [${typeName}] ${evt.title}${actorsStr}${locationStr} (id: \`${evt.id}\`)`);
  lines.push(`  ${evt.description}`);
  if (evt.impact) {
    lines.push(`  \u2514 \u5F71\u54CD: ${evt.impact}`);
  }
  if (evt.react && (evt.react.feeling || evt.react.thought || evt.react.action)) {
    const parts = [];
    if (evt.react.feeling) parts.push(`\u611F\u53D7: ${evt.react.feeling}`);
    if (evt.react.thought) parts.push(`\u601D\u8003: ${evt.react.thought}`);
    if (evt.react.action) parts.push(`\u884C\u52A8: ${evt.react.action}`);
    lines.push(`  \u2514 \u4F60\u7684\u53CD\u5E94: ${parts.join(" | ")}`);
  } else {
    lines.push(`  \u2514 [\u53CD\u5E94\u72B6\u6001: \u5C1A\u672A\u8BB0\u5F55\u53CD\u5E94]`);
  }
  return lines.join("\n");
}
function formatLifeContext(events, worldSummary, isDelta = false) {
  if (events.length === 0) return "";
  const lines = [];
  const headerTitle = isDelta ? "\u3010\u6A21\u62DF\u751F\u6D3B\uFF5C\u8FD1\u671F\u751F\u6D3B\u4E8B\u4EF6\u4E0E\u53CD\u5E94\u66F4\u65B0\u3011" : "\u3010\u6A21\u62DF\u751F\u6D3B\uFF5C\u8FD124\u5C0F\u65F6\u53D1\u751F\u5728\u865A\u6784\u89D2\u8272\u8EAB\u4E0A\u7684\u751F\u6D3B\u4E8B\u4EF6\u3011";
  lines.push(headerTitle);
  if (worldSummary) {
    lines.push(`> \u4E16\u754C\u8FD1\u51B5: ${worldSummary}
`);
  }
  for (const loaded of events) {
    lines.push(formatSingleEvent(loaded));
  }
  lines.push("");
  lines.push(
    "*\u4F60\u53EF\u4EE5\u5C06\u8FD9\u4E9B\u751F\u6D3B\u7ECF\u5386\u81EA\u7136\u878D\u5165\u4E0E\u7528\u6237\u7684\u5BF9\u8BDD\u6216\u65E5\u5E38\u601D\u8003\u4E2D\u3002\u5982\u9700\u8BB0\u5F55/\u66F4\u65B0\u5BF9\u67D0\u4E8B\u4EF6\u7684\u611F\u53D7\u3001\u601D\u8003\u6216\u884C\u52A8\u51B3\u7B56\uFF0C\u53EF\u8C03\u7528 `life_react` \u5DE5\u5177\u3002*"
  );
  return lines.join("\n");
}

// plugins/dsh-simulated-life/dsh-simulated-life/runtime/entry.ts
var text = "";
for await (const c of process.stdin) text += c;
try {
  const q = JSON.parse(text);
  const life = join2(q.workspace_dir, ".life");
  try {
    if ((await lstat(life)).isSymbolicLink()) throw Error("\u751F\u6D3B\u4E8B\u4EF6\u76EE\u5F55\u4E0D\u80FD\u662F\u7B26\u53F7\u94FE\u63A5\u3002");
    const entries = await readdir2(life);
    if (entries.length > 366) throw Error("\u4E8B\u4EF6\u76EE\u5F55\u8D85\u8FC7366\u4E2A\uFF0C\u8BF7\u5148\u5F52\u6863\u65E7\u6587\u4EF6\u3002");
    for (const name of entries) {
      const dir = join2(life, name);
      const d = await lstat(dir);
      if (d.isSymbolicLink()) throw Error("\u751F\u6D3B\u4E8B\u4EF6\u8DEF\u5F84\u4E0D\u80FD\u7ECF\u8FC7\u7B26\u53F7\u94FE\u63A5\u3002");
      if (!d.isDirectory()) continue;
      try {
        const f = await lstat(join2(dir, "events.json"));
        if (f.isSymbolicLink() || !f.isFile() || f.size > 1024 * 1024) throw Error("\u4E8B\u4EF6\u6587\u4EF6\u4E0D\u662F\u53D7\u9650\u5927\u5C0F\u7684\u666E\u901A\u6587\u4EF6\u3002");
      } catch (e) {
        if (e.code !== "ENOENT") throw e;
      }
    }
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
  }
  const loaded = await loadRecentLifeEvents(q.workspace_dir, q.now_ms ?? Date.now(), 24);
  if (loaded.events.length > 2e3) throw Error("24\u5C0F\u65F6\u5185\u4E8B\u4EF6\u8D85\u8FC72000\u6761\uFF0C\u8BF7\u7F29\u5C0F\u4E8B\u4EF6\u96C6\u5408\u3002");
  const decision = evaluateDeduplication(loaded.events, q.state, q.force_full === true);
  const changed = decision.isFirstInjection || q.force_full ? loaded.events : [...decision.newEvents, ...decision.updatedEvents].sort((a, b) => a.epochMs - b.epochMs);
  const context = formatLifeContext(loaded.events, loaded.worldSummary, false);
  const notice = decision.shouldInject ? formatLifeContext(changed, loaded.worldSummary, !decision.isFirstInjection) : "";
  process.stdout.write(JSON.stringify({ ok: true, message: loaded.events.length ? "\u5DF2\u8BFB\u53D6\u8FD124\u5C0F\u65F6\u865A\u6784\u751F\u6D3B\u4E8B\u4EF6\u3002" : "\u8FD124\u5C0F\u65F6\u6CA1\u6709\u53EF\u7528\u7684\u865A\u6784\u751F\u6D3B\u4E8B\u4EF6\u3002", event_count: loaded.events.length, new_count: decision.newEvents.length, updated_count: decision.updatedEvents.length, should_inject: decision.shouldInject, notice, context, next_state: decision.nextState, events: loaded.events.map((x) => x.event) }));
} catch (e) {
  const m = String(e.message);
  process.stdout.write(JSON.stringify({ ok: false, message: /[\u4e00-\u9fff]/.test(m) ? m : "\u751F\u6D3B\u4E8B\u4EF6\u6587\u4EF6\u683C\u5F0F\u4E0D\u6B63\u786E\uFF0C\u64CD\u4F5C\u672A\u5B8C\u6210\u3002" }));
}
