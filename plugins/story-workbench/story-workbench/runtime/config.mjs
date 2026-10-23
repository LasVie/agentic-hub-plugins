export default {
  "slug": "story-workbench",
  "version": "1.0.0",
  "name": "小说创作台",
  "description": "管理本地小说项目、人物、章节与修订历史；在中文编辑器中添加可重新定位的原文批注，不自动生成或改写正文。",
  "actions": [
    "status",
    "create_project",
    "save_character",
    "save_chapter",
    "annotate",
    "resolve_annotation",
    "export_project"
  ],
  "help": {
    "help": "查看本工具操作说明。",
    "open_ui": "为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。",
    "stop_ui": "关闭本插件该工作目录的界面服务，保留数据。",
    "status": "读取项目、人物、章节、原文批注与修订历史。",
    "create_project": "expected_revision, name；一个工作目录一个项目，不覆盖已有项目。",
    "save_character": "expected_revision, id, name, role, goal；保存/修改人物设定。",
    "save_chapter": "expected_revision, id, title, content, chapter_revision（更新已有章节时必填其hash）；保存旧版本并重新定位批注。",
    "annotate": "expected_revision, chapter_id, chapter_revision, quote, note, start_hint/end_hint（可选，JavaScript UTF-16索引）；仅可批注已保存原文。",
    "resolve_annotation": "expected_revision, annotation_id；标记解决并保留记录。",
    "export_project": "导出完整项目与历史；不生成正文。"
  },
  "initial": {
    "schema": 1,
    "project_name": "",
    "characters": [],
    "chapters": [],
    "annotations": [],
    "history": []
  },
  "bundle_id": "e23ec60f024e1db456efcaf32e758158bd907100f376eb0c87c085d45c5aa150"
};
