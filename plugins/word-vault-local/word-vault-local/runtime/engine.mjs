// Adapted 2026-10-23 from dsh-word-vault (MIT, wangzhanchao883):
// word normalization and per-learner occurrence / three-correct mastery semantics.
// Native SQLite state, revision guards and quiz API are new; no borrowed card layout.
import { lemmaOf } from '../vendor/words.mjs';
import { text, id, integer, fail, now, object } from './common.mjs';
import { randomInt, randomBytes } from 'node:crypto';
const shuffle = a => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = randomInt(i + 1); [b[i], b[j]] = [b[j], b[i]]; } return b; };
function learner(p) { return id(p.learner || 'learner-1', '学习者编号'); }
function view(ctx, who) {
  const { state, revision } = ctx.read();
  const words = state.words.filter(w => w.learner === who);
  const quiz = state.quizzes.filter(q => q.learner === who).at(-1);
  return { revision, learner: who, words, summary: { total: words.length, mastered: words.filter(w => w.streak >= 3).length, wrong: words.filter(w => w.wrong_count > 0).length }, quiz: quiz ? { id: quiz.id, correct: quiz.correct, finished: quiz.finished, questions: quiz.questions.map(q => ({ id: q.id, term: q.term, options: q.options, chosen_index: q.chosen_index ?? null, is_correct: q.is_correct ?? null, correct_meaning: q.chosen_index === undefined ? undefined : q.options[q.answer_index] })) } : null };
}
export function execute(ctx, action, p) {
  if (!object(p)) fail('payload 须为对象。');
  const who = learner(p);
  if (action === 'status') return view(ctx, who);
  if (action === 'add_words') {
    if (!Array.isArray(p.entries) || p.entries.length < 1 || p.entries.length > 50) fail('每次须提供 1 至 50 个 entries 词条。');
    const entries = p.entries.map(e => {
      if (!object(e)) fail('每个词条须含 term 与 meaning。');
      const term = text(e.term, '单词或词组', 80).toLowerCase().replace(/\s+/g, ' ');
      if (!/^[a-z]+(?:[ '\u2019-][a-z]+)*$/.test(term)) fail('词条须为英文单词或词组。');
      return { term, lemma: term.includes(' ') ? term : lemmaOf(term), meaning: text(e.meaning, '中文释义', 200) };
    });
    ctx.mutate(p.expected_revision, s => {
      for (const e of entries) {
        let w = s.words.find(w => w.learner === who && w.lemma === e.lemma);
        if (!w) { if (s.words.length >= 1500) fail('词库已达 1500 条上限，请换用其他工作目录。'); w = { id: 'w-' + randomBytes(6).toString('hex'), learner: who, ...e, seen_count: 0, streak: 0, wrong_count: 0 }; s.words.push(w); }
        if (w.meaning !== e.meaning && w.seen_count > 0) { w.streak = 0; w.status = 'learning'; }
        w.term = e.term; w.meaning = e.meaning; w.seen_count++; w.updated_at = now(); w.status = w.streak >= 3 ? 'mastered' : 'learning';
      }
      return { message: `已保存并计次 ${entries.length} 个词条。` };
    });
    return { message: `已保存并计次 ${entries.length} 个词条。`, ...view(ctx, who) };
  }
  if (action === 'start_quiz') {
    ctx.mutate(p.expected_revision, s => {
      const all = s.words.filter(w => w.learner === who);
      if (new Set(all.map(w => w.meaning)).size < 4) fail('至少需要四个不同释义的词条，才能生成四选一练习。');
      if (p.wrong_only !== undefined && typeof p.wrong_only !== 'boolean') fail('wrong_only 须为布尔值。');
      const pool = p.wrong_only ? all.filter(w => w.wrong_count > 0) : all;
      if (!pool.length) fail('当前没有错词，可先开始普通练习。');
      const size = Math.min(integer(p.size ?? 4, '练习题数', 1, 10), pool.length);
      const questions = shuffle(pool).slice(0, size).map((w, i) => {
        const alternatives = shuffle([...new Set(all.filter(x => x.meaning !== w.meaning).map(x => x.meaning))]).slice(0, 3);
        const options = shuffle([w.meaning, ...alternatives]);
        return { id: i, word_id: w.id, term: w.term, options, answer_index: options.indexOf(w.meaning) };
      });
      if (s.quizzes.length >= 150) fail('练习记录已满；请导出并另建工作目录。');
      s.quizzes.push({ id: 'quiz-' + randomBytes(6).toString('hex'), learner: who, correct: 0, finished: false, created_at: now(), questions });
      return {};
    });
    return { message: '练习已生成，答案由本地记录核对。', ...view(ctx, who) };
  }
  if (action === 'answer') {
    const result = ctx.mutate(p.expected_revision, s => {
      const q = s.quizzes.find(q => q.id === p.quiz_id && q.learner === who);
      if (!q) fail('练习不存在或不属于此学习者。');
      const n = integer(p.question_id, '题号', 0, q.questions.length - 1), question = q.questions[n];
      if (question.chosen_index !== undefined) fail('这道题已经作答，不会重复计分。');
      const choice = integer(p.option_index, '选项', 0, 3), w = s.words.find(w => w.id === question.word_id);
      if (!w || w.meaning !== question.options[question.answer_index]) fail('词条释义已有变更，请重新开始练习。');
      question.chosen_index = choice; question.is_correct = choice === question.answer_index;
      if (question.is_correct) { q.correct++; w.streak++; } else { w.streak = 0; w.wrong_count++; }
      w.status = w.streak >= 3 ? 'mastered' : 'learning';
      q.finished = q.questions.every(x => x.chosen_index !== undefined);
      return { message: question.is_correct ? '答对了。' : `本题正确释义：${w.meaning}`, is_correct: question.is_correct };
    });
    return { ...result, ...view(ctx, who) };
  }
  if (action === 'export_bank') return { message: '导出数据仅包含当前学习者，不含其他人的练习。', export: view(ctx, who) };
  fail('操作不支持。');
}
