export default {
  "slug": "git-branch-atlas",
  "version": "1.0.0",
  "name": "Git 分支全景",
  "description": "只读本地 Git 分支拓扑、父提交与关联工作树，比较两个引用的独有提交和共同祖先，提供可搜索、可点选的中文图谱。",
  "actions": [
    "status",
    "scan",
    "compare_branches",
    "export_graph"
  ],
  "help": {
    "help": "查看本工具操作说明。",
    "open_ui": "为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。",
    "stop_ui": "关闭本插件该工作目录的界面服务，保留数据。",
    "status": "读取上一份已保存分支图。",
    "scan": "expected_revision, repo_dir（工作区内相对目录，默认.）, limit（1至200）；只读分支、提交parent、泳道与关联工作树。",
    "compare_branches": "repo_dir, base, head；引用先解析完整提交OID，再计算base_only/head_only/merge_bases，不联网取对象。",
    "export_graph": "导出已有图数据。不支持checkout/fetch/commit/删除/文件blame。"
  },
  "initial": {
    "schema": 1,
    "snapshot": null
  },
  "bundle_id": "ab076d94f016bf5e2af6d83aa58cb9eab43e1bfdf185074dcd6be99eeeb05dc2"
};
