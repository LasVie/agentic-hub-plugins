export default {
  "slug": "word-vault-local",
  "version": "1.0.0",
  "name": "词汇练习室",
  "description": "按学习者保存英文词条、出现次数与连对掌握状态；在中文交互界面完成四选一、错词复习和导出，无需额外账号。",
  "actions": [
    "status",
    "add_words",
    "start_quiz",
    "answer",
    "export_bank"
  ],
  "help": {
    "help": "查看本工具操作说明。",
    "open_ui": "为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。",
    "stop_ui": "关闭本插件该工作目录的界面服务，保留数据。",
    "status": "learner（默认 learner-1）；返回该学习者词库、统计与最近练习，不公开未答题目的答案索引。",
    "add_words": "expected_revision, learner, entries:[{term,meaning}]，每次1至50条；重复词元计次，释义修改会重置掌握状态。",
    "start_quiz": "expected_revision, learner, size（1至10，默认4）, wrong_only（可选）；四个不同释义才可出题。",
    "answer": "expected_revision, learner, quiz_id, question_id, option_index（0至3）；答案按本地保存的题目核对，三次连对掌握。",
    "export_bank": "learner；导出该学习者词库。"
  },
  "initial": {
    "schema": 1,
    "words": [],
    "quizzes": []
  },
  "bundle_id": "95c50f5528984ef1d252394f6b47aed12c37a1e3b3a1b6a66f2d7d54008cb4e8"
};
