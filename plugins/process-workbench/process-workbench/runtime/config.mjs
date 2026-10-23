export default {
  "slug": "process-workbench",
  "version": "1.0.0",
  "name": "流程执行台",
  "description": "校验多阶段流程模板，冻结每次运行快照，以实际文件 SHA-256 记录环节完成证据，提供中文交互看板。",
  "actions": [
    "status",
    "validate_template",
    "save_template",
    "start_run",
    "complete_step",
    "resume_run",
    "export_process"
  ],
  "help": {
    "help": "查看本工具操作说明。",
    "open_ui": "为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。",
    "stop_ui": "关闭本插件该工作目录的界面服务，保留数据。",
    "status": "读取当前模板与运行记录。",
    "validate_template": "template 为 JSON对象：process:{name}, phases:[{id,name,links:[{id,name,prompt,on_success}]}]；支持 next/end/break/goto:环节id。",
    "save_template": "expected_revision, template；校验后保存，既有运行不会换用新模板。",
    "start_run": "expected_revision, run_id；创建唯一运行编号并冻结模板。",
    "complete_step": "expected_revision, run_id, step_id, note, evidence_files（1至10个工作区内相对文件路径）；记录真实文件SHA-256后流转，不能跳步骤。",
    "resume_run": "expected_revision, run_id；显式恢复暂停运行。",
    "export_process": "导出模板、快照与文件证据；不执行命令、模型或代理。"
  },
  "initial": {
    "schema": 1,
    "template": null,
    "runs": []
  },
  "bundle_id": "ac8749de3e864bd772428ad7bc132e6de7b9935d3f228df22b61266698e1b179"
};
