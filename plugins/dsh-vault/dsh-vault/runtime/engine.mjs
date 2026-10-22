// WorkSwarm port. Upstream MIT sources and notices are bundled in vendor/ and licenses/.

// plugins/dsh-vault/dsh-vault/runtime/entry.ts
import { readFile, writeFile, rename, mkdir, stat, lstat, chmod } from "node:fs/promises";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

// plugins/dsh-vault/dsh-vault/vendor/crypto.ts
import {
  createCipheriv,
  createDecipheriv,
  randomBytes,
  scrypt as scryptCallback,
  timingSafeEqual
} from "node:crypto";
import { promisify } from "node:util";
var scrypt = promisify(scryptCallback);
var KEY_LENGTH = 32;
var IV_LENGTH = 12;
var SCRYPT_N = 2 ** 15;
var SCRYPT_R = 8;
var SCRYPT_P = 1;
var SCRYPT_MAXMEM = 1024 * 1024 * 1024;
async function deriveKey(masterPassword, params) {
  const salt = Buffer.from(params.saltHex, "hex");
  return scrypt(masterPassword, salt, KEY_LENGTH, {
    N: params.n,
    r: params.r,
    p: params.p,
    maxmem: SCRYPT_MAXMEM
  });
}
function newKdfParams() {
  return {
    algo: "scrypt",
    n: SCRYPT_N,
    r: SCRYPT_R,
    p: SCRYPT_P,
    saltHex: randomBytes(16).toString("hex")
  };
}
function encrypt(plaintext, key) {
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const data = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();
  return { ivHex: iv.toString("hex"), tagHex: tag.toString("hex"), dataHex: data.toString("hex") };
}
function decrypt(blob, key) {
  const decipher = createDecipheriv("aes-256-gcm", key, Buffer.from(blob.ivHex, "hex"));
  decipher.setAuthTag(Buffer.from(blob.tagHex, "hex"));
  return Buffer.concat([
    decipher.update(Buffer.from(blob.dataHex, "hex")),
    decipher.final()
  ]);
}

// plugins/dsh-vault/dsh-vault/vendor/totp.ts
import { createHmac, randomBytes as randomBytes2 } from "node:crypto";
var DEFAULT_PERIOD_SECONDS = 30;
var DEFAULT_DIGITS = 6;
var BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
function base32Decode(input2) {
  const cleaned = input2.replace(/[\s-]/g, "").replace(/=+$/, "").toUpperCase();
  if (cleaned.length === 0) {
    throw new Error("invalid Base32 secret: secret is empty");
  }
  if (cleaned.length < 8) {
    throw new Error("invalid Base32 secret: too short (expected at least 8 characters)");
  }
  if (!/^[A-Z2-7]+$/.test(cleaned)) {
    throw new Error("invalid Base32 secret: contains characters outside A-Z2-7");
  }
  let bits = 0;
  let value = 0;
  const bytes = [];
  for (const char of cleaned) {
    const index = BASE32_ALPHABET.indexOf(char);
    if (index < 0) throw new Error(`invalid Base32 character: ${char}`);
    value = value << 5 | index;
    bits += 5;
    if (bits >= 8) {
      bytes.push(value >>> bits - 8 & 255);
      bits -= 8;
    }
  }
  return Buffer.from(bytes);
}
function digitsOf(raw) {
  if (raw === void 0) return DEFAULT_DIGITS;
  const parsed = Number.parseInt(raw, 10);
  if (Number.isInteger(parsed) && parsed >= 6 && parsed <= 10) return parsed;
  return DEFAULT_DIGITS;
}
function periodOf(raw) {
  if (raw === void 0) return DEFAULT_PERIOD_SECONDS;
  const parsed = Number.parseInt(raw, 10);
  if (Number.isInteger(parsed) && parsed >= 5) return parsed;
  return DEFAULT_PERIOD_SECONDS;
}
function parseTotpSecret(input2) {
  const trimmed = input2.trim();
  if (trimmed.startsWith("otpauth://")) {
    const url = new URL(trimmed);
    if (url.protocol !== "otpauth:" || url.host !== "totp") {
      throw new Error("unsupported otpauth URI: only otpauth://totp is supported");
    }
    const secret = url.searchParams.get("secret");
    if (!secret) throw new Error("otpauth URI is missing the secret parameter");
    const label = decodeURIComponent(url.pathname.replace(/^\//, ""));
    const colon = label.indexOf(":");
    const issuer = url.searchParams.get("issuer") ?? (colon >= 0 ? label.slice(0, colon) : void 0);
    const account = colon >= 0 ? label.slice(colon + 1) : label;
    return {
      secret,
      periodSeconds: periodOf(url.searchParams.get("period") ?? void 0),
      digits: digitsOf(url.searchParams.get("digits") ?? void 0),
      ...issuer !== void 0 ? { issuer } : {},
      ...account !== void 0 && account.length > 0 ? { account } : {}
    };
  }
  return {
    secret: trimmed,
    periodSeconds: DEFAULT_PERIOD_SECONDS,
    digits: DEFAULT_DIGITS
  };
}
function hotp(secret, counter, digits) {
  const counterBuffer = Buffer.alloc(8);
  counterBuffer.writeBigUInt64BE(BigInt(Math.floor(counter)));
  const hmac = createHmac("sha1", secret).update(counterBuffer).digest();
  const offset = hmac[hmac.length - 1] & 15;
  const binary = (hmac[offset] & 127) << 24 | (hmac[offset + 1] & 255) << 16 | (hmac[offset + 2] & 255) << 8 | hmac[offset + 3] & 255;
  return (binary % 10 ** digits).toString().padStart(digits, "0");
}
function totp(input2, nowMs = Date.now()) {
  const parsed = parseTotpSecret(input2);
  const key = base32Decode(parsed.secret);
  const counter = Math.floor(nowMs / 1e3 / parsed.periodSeconds);
  return hotp(key, counter, parsed.digits);
}

// plugins/dsh-vault/dsh-vault/runtime/entry.ts
var text = "";
for await (const chunk of process.stdin) text += chunk;
var input = JSON.parse(text);
async function main(q) {
  const dir = q.directory;
  const file = join(dir, "vault.json");
  const save = async (header2, data2, key2) => {
    const encrypted = encrypt(Buffer.from(JSON.stringify(data2)), key2);
    const temp = join(dir, `pending-${randomUUID()}.json`);
    await writeFile(temp, JSON.stringify({ ...header2, encrypted }), { flag: "wx", mode: 384 });
    await rename(temp, file);
    await chmod(file, 384);
  };
  if (typeof q.master_password !== "string" || q.master_password.length < 12) throw Error("\u4E3B\u53E3\u4EE4\u81F3\u5C11\u9700\u898112\u4E2A\u5B57\u7B26\uFF0C\u8BF7\u5728\u672C\u5730\u914D\u7F6E\u3002");
  await mkdir(dir, { recursive: true, mode: 448 });
  if ((await lstat(dir)).isSymbolicLink()) throw Error("\u4FDD\u9669\u5E93\u76EE\u5F55\u4E0D\u80FD\u662F\u7B26\u53F7\u94FE\u63A5\u3002");
  if (q.action === "init") {
    try {
      await lstat(file);
      throw Error("\u4FDD\u9669\u5E93\u5DF2\u5B58\u5728\uFF0C\u4E0D\u80FD\u8986\u76D6\u521D\u59CB\u5316\u3002");
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
    }
    const kdf = newKdfParams();
    const key2 = await deriveKey(q.master_password, kdf);
    await save({ version: 1, kdf }, { entries: {} }, key2);
    key2.fill(0);
    return { ok: true, message: "\u672C\u5730\u52A0\u5BC6\u4FDD\u9669\u5E93\u5DF2\u5EFA\u7ACB\u3002", directory: dir };
  }
  if ((await lstat(file)).isSymbolicLink() || (await stat(file)).size > 2 * 1024 * 1024) throw Error("\u4FDD\u9669\u5E93\u6587\u4EF6\u8DEF\u5F84\u6216\u5927\u5C0F\u4E0D\u6B63\u786E\u3002");
  const header = JSON.parse(await readFile(file, "utf8"));
  const k = header.kdf;
  if (header.version !== 1 || k?.algo !== "scrypt" || k.n !== 32768 || k.r !== 8 || k.p !== 1 || !/^[0-9a-f]{32}$/.test(k.saltHex)) throw Error("\u4FDD\u9669\u5E93\u683C\u5F0F\u6216\u5BC6\u94A5\u53C2\u6570\u4E0D\u53D7\u652F\u6301\u3002");
  const key = await deriveKey(q.master_password, k);
  let data;
  try {
    data = JSON.parse(decrypt(header.encrypted, key).toString("utf8"));
  } catch {
    key.fill(0);
    throw Error("\u4E3B\u53E3\u4EE4\u4E0D\u6B63\u786E\u6216\u4FDD\u9669\u5E93\u5185\u5BB9\u5DF2\u88AB\u4FEE\u6539\u3002");
  }
  try {
    const id = q.id;
    if (!data.entries || typeof data.entries !== "object" || Array.isArray(data.entries)) throw Error("\u4FDD\u9669\u5E93\u5185\u90E8\u683C\u5F0F\u4E0D\u6B63\u786E\u3002");
    if (q.action === "list") return { ok: true, message: "\u5DF2\u8BFB\u53D6\u4FDD\u9669\u5E93\u6761\u76EE\uFF0C\u672A\u8FD4\u56DE\u79D8\u5BC6\u3002", entries: Object.values(data.entries).filter((x) => String(x.label).includes(q.query ?? "")).map((e) => ({ id: e.id, label: e.label, username: e.username, secret: "********", has_totp: !!e.totp_secret })) };
    if (typeof id !== "string" || !/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(id)) throw Error("\u6761\u76EE ID \u53EA\u80FD\u4F7F\u7528\u5B57\u6BCD\u3001\u6570\u5B57\u3001\u4E0B\u5212\u7EBF\u4E0E\u77ED\u6A2A\u7EBF\uFF0C\u6700\u957F64\u5B57\u7B26\u3002");
    const found = Object.prototype.hasOwnProperty.call(data.entries, id) ? data.entries[id] : void 0;
    if (q.action === "put") {
      const c = q.credential;
      if (!c || typeof c.label !== "string" || !c.label || typeof c.secret !== "string" || !c.secret || JSON.stringify(c).length > 2e4) throw Error("\u672C\u5730\u51ED\u636E\u6587\u4EF6\u5FC5\u987B\u5305\u542B label \u548C secret\uFF0C\u4E14\u5927\u5C0F\u53D7\u9650\u3002");
      if (c.totp_secret) try {
        totp(c.totp_secret);
      } catch {
        throw Error("\u52A8\u6001\u9A8C\u8BC1\u7801\u5BC6\u94A5\u683C\u5F0F\u4E0D\u6B63\u786E\u3002");
      }
      if (found && !q.overwrite) throw Error("\u8BE5\u6761\u76EE\u5DF2\u5B58\u5728\uFF1B\u660E\u786E\u8BBE\u7F6E overwrite \u624D\u80FD\u66F4\u65B0\u3002");
      data.entries[id] = { id, label: c.label, username: String(c.username ?? ""), secret: c.secret, ...c.totp_secret ? { totp_secret: c.totp_secret } : {}, updated_at: (/* @__PURE__ */ new Date()).toISOString() };
      await save({ version: 1, kdf: k }, data, key);
      return { ok: true, message: "\u51ED\u636E\u5DF2\u52A0\u5BC6\u4FDD\u5B58\uFF0C\u672A\u8FD4\u56DE\u79D8\u5BC6\u3002", id };
    }
    if (!found) throw Error("\u672A\u627E\u5230\u8BE5\u51ED\u636E\u6761\u76EE\u3002");
    if (q.action === "get") return { ok: true, message: "\u51ED\u636E\u5DF2\u8BFB\u53D6\uFF0C\u79D8\u5BC6\u5DF2\u63A9\u7801\u3002", entry: { id, label: found.label, username: found.username, secret: "********", has_totp: !!found.totp_secret } };
    if (q.action === "totp") {
      if (!found.totp_secret) throw Error("\u8BE5\u51ED\u636E\u6CA1\u6709\u52A8\u6001\u9A8C\u8BC1\u7801\u5BC6\u94A5\u3002");
      return { ok: true, message: "\u5DF2\u5728\u672C\u5730\u751F\u6210\u5F53\u524D\u52A8\u6001\u9A8C\u8BC1\u7801\uFF0C\u8BF7\u52FF\u5BF9\u5916\u5206\u4EAB\u3002", id, code: totp(found.totp_secret, q.now_ms ?? Date.now()) };
    }
    if (q.action === "remove") {
      if (q.confirm !== true) throw Error("\u5220\u9664\u9700\u8981\u660E\u786E\u8BBE\u7F6E confirm=true\u3002");
      delete data.entries[id];
      await save({ version: 1, kdf: k }, data, key);
      return { ok: true, message: "\u51ED\u636E\u5DF2\u4ECE\u52A0\u5BC6\u4FDD\u9669\u5E93\u79FB\u9664\u3002", id };
    }
    throw Error("\u4E0D\u652F\u6301\u8BE5\u4FDD\u9669\u5E93\u64CD\u4F5C\u3002");
  } finally {
    key.fill(0);
  }
}
try {
  process.stdout.write(JSON.stringify(await main(input)));
} catch (e) {
  const m = String(e.message);
  process.stdout.write(JSON.stringify({ ok: false, message: /[\u4e00-\u9fff]/.test(m) ? m : "\u4FDD\u9669\u5E93\u6587\u4EF6\u4E0D\u53EF\u8BFB\u6216\u683C\u5F0F\u9519\u8BEF\uFF0C\u64CD\u4F5C\u672A\u5B8C\u6210\u3002" }));
}
