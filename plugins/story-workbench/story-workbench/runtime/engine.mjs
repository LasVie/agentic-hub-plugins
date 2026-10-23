// OpenWrite Studio subset adaptation, 2026-10-23. MIT, OpenWrite contributors.
// Uses the unmodified MIT quote anchoring and manuscript marker cores.
import { locateQuote } from '../vendor/manuscript-selection.ts';
import { readableWritingUnits, parseMarkers } from '../vendor/manuscript-markers.ts';
import { text, id, fail, hash, now, object } from './common.mjs';
import { randomBytes } from 'node:crypto';
function view(ctx) { const { state, revision } = ctx.read(); return { revision, ...state, chapters: state.chapters.map(c => ({ ...c, writing_units: readableWritingUnits(c.content), markers: parseMarkers(c.content) })) }; }
export function execute(ctx, action, p) {
  if (!object(p)) fail('payload 须为对象。');
  if (action === 'status') return view(ctx);
  if (action === 'export_project') return { export: view(ctx), message: '项目文本和历史已导出；未运行写作或审稿模型。' };
  const result = ctx.mutate(p.expected_revision, s => {
    if (action === 'create_project') {
      if (s.project_name) fail('此工作目录已有项目，不会覆盖；请编辑现有项目或使用另一个目录。');
      s.project_name = text(p.name, '项目名', 120); return { message: '项目已创建。' };
    }
    if (!s.project_name) fail('请先创建项目。');
    if (action === 'save_character') {
      const key = id(p.id, '人物编号');
      const c = { id: key, name: text(p.name, '人物名', 80), role: text(p.role || '', '身份', 300, true), goal: text(p.goal || '', '动机与目标', 2000, true), updated_at: now() };
      const pos = s.characters.findIndex(x => x.id === key);
      if (pos < 0) { if (s.characters.length >= 100) fail('人物数量已达 100。'); s.characters.push(c); } else s.characters[pos] = c;
      return { message: '人物设定已保存。' };
    }
    if (action === 'save_chapter') {
      const key = id(p.id, '章节编号'), title = text(p.title, '章节标题', 160);
      if (typeof p.content !== 'string' || p.content.length > 50000 || p.content.includes('\0')) fail('章节正文须为最多 50000 字的文本。');
      const old = s.chapters.find(c => c.id === key);
      if (old && p.chapter_revision !== old.hash) fail('章节版本已更新，请刷新后重试。');
      if (!old && p.chapter_revision) fail('新章节不能指定旧版本。');
      if (old) { if (s.history.length >= 100) fail('修订历史已达 100 份，请先导出整理。'); s.history.push({ ...old, saved_at: now() }); }
      else if (s.chapters.length >= 100) fail('章节数量已达 100。');
      const chapter = { id: key, title, content: p.content, hash: hash(p.content), updated_at: now() };
      if (old) s.chapters[s.chapters.indexOf(old)] = chapter; else s.chapters.push(chapter);
      for (const a of s.annotations.filter(a => a.chapter_id === key)) a.anchor = locateQuote(chapter.content, a.quote, a.anchor.start ?? -1, a.anchor.end ?? -1);
      return { message: '章节已保存，旧版本保留在修订历史。', chapter_hash: chapter.hash };
    }
    if (action === 'annotate') {
      const chapter = s.chapters.find(c => c.id === p.chapter_id);
      if (!chapter || p.chapter_revision !== chapter.hash) fail('请先保存并确认当前章节版本，再添加批注。');
      const quote = text(p.quote, '选中原文', 2000), note = text(p.note, '批注内容', 2000);
      const anchor = locateQuote(chapter.content, quote, p.start_hint ?? -1, p.end_hint ?? -1);
      if (anchor.state === 'detached') fail(anchor.reason === 'ambiguous' ? '原文出现多次，请在编辑器中精确选择后再批注。' : '选中文本不在当前已保存正文中。');
      if (s.annotations.length >= 500) fail('批注已达 500 条。');
      const a = { id: 'ann-' + randomBytes(6).toString('hex'), chapter_id: chapter.id, source_revision: chapter.hash, quote, note, anchor, status: 'open', created_at: now() };
      s.annotations.push(a); return { message: '原文批注已保存。', annotation_id: a.id };
    }
    if (action === 'resolve_annotation') {
      const a = s.annotations.find(a => a.id === p.annotation_id); if (!a) fail('批注不存在。');
      a.status = 'resolved'; return { message: '批注已标记解决；记录仍保留。' };
    }
    fail('操作不支持。');
  });
  return { ...result, ...view(ctx) };
}
