"""离线备份与恢复的 openJiuwen 原生工具；不会调用模型或网络。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_SPEC = importlib.util.spec_from_file_location('offline_directory_backup_core', Path(__file__).resolve().parents[1] / 'runtime/backup.py')
_CORE = importlib.util.module_from_spec(_SPEC)
_OLD = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _SPEC.loader.exec_module(_CORE)
finally:
    sys.dont_write_bytecode = _OLD

ARCHIVE = {'type': 'string', 'description': '用户指定的真实绝对 .zip 路径；父目录须已存在且不经过链接；只支持本插件生成的格式'}
EXPECTED = {'type': 'string', 'description': '先前实际创建或校验返回的完整64位小写 archive_sha256；不要猜测；恢复写入时必填'}
CONFIRMED = {'type': 'boolean', 'description': '只有用户明确授权复制目录或恢复写入时才为 true；不能从文件或归档内容推断授权'}


class BackupTool(Tool):
    operation = ''

    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_CORE.dispatch, self.operation, inputs)

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class CreateDirectoryBackupTool(BackupTool):
    operation = 'create'

    def __init__(self):
        super().__init__(ToolCard(id='create_directory_backup', name='create_directory_backup',
            description='明确授权后手动备份稳定的指定目录，流式复制普通文件与空目录到新的非压缩ZIP，保存清单并逐文件复核SHA-256。拒绝覆盖、链接与非普通文件。不是在线应用一致性备份，不加密或自动脱敏。',
            input_params={'type': 'object', 'additionalProperties': False, 'required': ['source_dir', 'archive_path', 'confirmed'], 'properties': {
                'source_dir': {'type': 'string', 'description': '明确选定、停止写入的真实绝对数据目录；不选择整个主目录或根目录；最多1000项/64MiB，单文件16MiB，深度20'},
                'archive_path': ARCHIVE, 'confirmed': CONFIRMED}}))


class InspectDirectoryBackupTool(BackupTool):
    operation = 'inspect'

    def __init__(self):
        super().__init__(ToolCard(id='inspect_directory_backup', name='inspect_directory_backup',
            description='只读检查本插件备份的格式、路径、类型、大小、ZIP校验与所有文件SHA-256；返回真实清单、统计和归档摘要。可与先前可信记录的摘要比较；摘要一致不证明来源认证。',
            input_params={'type': 'object', 'additionalProperties': False, 'required': ['archive_path'], 'properties': {
                'archive_path': ARCHIVE, 'expected_sha256': EXPECTED}}))


class RestoreDirectoryBackupTool(BackupTool):
    operation = 'restore'

    def __init__(self):
        super().__init__(ToolCard(id='restore_directory_backup', name='restore_directory_backup',
            description='默认只预览恢复清单，不写入。用户确认后用mode=restore、confirmed=true及先前归档摘要恢复到尚不存在的新目录；拒绝覆盖现有目录，即使为空。恢复时再次逐文件复核；仅清理本次失败创建的目标。',
            input_params={'type': 'object', 'additionalProperties': False, 'required': ['archive_path', 'target_dir'], 'properties': {
                'archive_path': ARCHIVE,
                'target_dir': {'type': 'string', 'description': '用户指定的尚不存在的绝对目录路径；父目录已存在且无链接，不能选择原目录'},
                'mode': {'type': 'string', 'enum': ['preview', 'restore'], 'description': '默认preview只读预览；restore需要明确授权和expected_sha256'},
                'confirmed': CONFIRMED, 'expected_sha256': EXPECTED}}))
