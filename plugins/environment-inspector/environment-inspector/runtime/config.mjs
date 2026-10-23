export default {
  "slug": "environment-inspector",
  "version": "1.0.0",
  "name": "本机环境探针",
  "description": "主动观测本机系统、标准位置工具链和 TCP 监听端口，保存与比较快照，提供中文筛选界面；不结束进程、不读取密钥。",
  "actions": [
    "status",
    "probe",
    "compare",
    "export_snapshots"
  ],
  "help": {
    "help": "查看本工具操作说明。",
    "open_ui": "为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。",
    "stop_ui": "关闭本插件该工作目录的界面服务，保留数据。",
    "status": "读取已保存观测快照。",
    "probe": "expected_revision；主动执行只读本机标准位置工具 --version 与 lsof TCP监听观测。失败保持unavailable，不代表系统没有服务。",
    "compare": "before_id, after_id；比较两份不同的已保存快照，端口不可观测时不推断增减。",
    "export_snapshots": "导出已保存快照，不读取密钥/配置文件/用户名/设备名/网卡地址。"
  },
  "initial": {
    "schema": 1,
    "snapshots": []
  },
  "bundle_id": "4637752f9fb396e64bcea261a47a96ac14e4ec3347bcb88e64eef86995c127c5"
};
