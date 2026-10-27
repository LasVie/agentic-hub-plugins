// 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版。
// 源：GoogleChrome/modern-web-guidance-src，提交 8a0a736723558e9ae484e4b6bbf3cc6a8d6ba4ad，src/rag/bm25.ts。
// Apache-2.0，完整许可见 ../licenses/modern-web-guidance-src/LICENSE。
// 去除类型、翻译注释/错误，添加中文双字分词；BM25 与 RRF 计算保持上游实现。
// 相同 ID 的多个块只保留最高分。
const STOPWORDS = new Set('the a an and or of to in for with on by is are be as it this that from at use using your you can how when which into not'.split(' '));
export const DEFAULT_BM25_K1 = 1.2;
export const DEFAULT_BM25_B = 0.75;
export const DEFAULT_RRF_K = 60;
export function tokenize(text) {
  const lower = text.toLowerCase();
  const latin = (lower.match(/[a-z0-9][a-z0-9-]+/g) ?? []).filter(t => !STOPWORDS.has(t));
  const chinese = [];
  for (const segment of lower.match(/\p{Script=Han}+/gu) ?? []) {
    const chars = [...segment];
    if (chars.length === 1) chinese.push(chars[0]);
    for (let i = 0; i < chars.length - 1; i++) chinese.push(chars[i] + chars[i + 1]);
  }
  return [...latin, ...chinese];
}
export function buildBm25Index(docs) {
  if (docs.length === 0) throw new Error('无法建立索引：没有指南。');
  const docFreq = new Map();
  const indexDocs = docs.map(doc => {
    const tokens = tokenize(doc.text);
    const freqs = new Map();
    for (const t of tokens) freqs.set(t, (freqs.get(t) ?? 0) + 1);
    for (const t of freqs.keys()) docFreq.set(t, (docFreq.get(t) ?? 0) + 1);
    return {id: doc.id, length: tokens.length, freqs};
  });
  const avgDocLength = indexDocs.reduce((sum, d) => sum + d.length, 0) / indexDocs.length;
  return {docs: indexDocs, docFreq, avgDocLength};
}
// 返回正分匹配项；同 ID 的块按最高分合并。
export function rankBm25(index, query, k1 = DEFAULT_BM25_K1, b = DEFAULT_BM25_B) {
  const n = index.docs.length;
  const termIdfs = [...new Set(tokenize(query))].map(term => {
    const df = index.docFreq.get(term) ?? 0;
    return {term, idf: Math.log(1 + (n - df + 0.5) / (df + 0.5))};
  });
  const bestById = new Map();
  for (const doc of index.docs) {
    let score = 0;
    for (const {term, idf} of termIdfs) {
      const f = doc.freqs.get(term);
      if (!f) continue;
      score += (idf * f * (k1 + 1)) / (f + k1 * (1 - b + (b * doc.length) / index.avgDocLength));
    }
    if (score > (bestById.get(doc.id) ?? 0)) bestById.set(doc.id, score);
  }
  return [...bestById].map(([id, score]) => ({id, score})).sort((x, y) => y.score - x.score);
}
// 保留上游倒数排名融合函数；本版没有语义检索分支，不调用它。
export function reciprocalRankFusion(rankings, k = DEFAULT_RRF_K) {
  const scores = new Map();
  for (const ranking of rankings) {
    ranking.forEach((id, i) => scores.set(id, (scores.get(id) ?? 0) + 1 / (k + i + 1)));
  }
  return [...scores].map(([id, score]) => ({id, score})).sort((x, y) => y.score - x.score);
}
