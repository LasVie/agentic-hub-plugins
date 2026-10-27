"""JiuwenSwarm 原生工具桥接。"""
import asyncio
import importlib.util
from pathlib import Path
from openjiuwen.core.foundation.tool import Tool, ToolCard

_spec = importlib.util.spec_from_file_location('anidoodle_runtime', Path(__file__).resolve().parents[1] / 'runtime.py')
_runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_runtime)

class AnidoodleTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(id='anidoodle_art', name='anidoodle_art', description='创建中文离线手绘互动 HTML 或导出可编辑源码。场景为鼠标跟随伙伴、表单伙伴、滚动逐笔绘画；不覆盖已有文件，不联网。', input_params={
            'type':'object','properties':{
                'action':{'type':'string','enum':['list','create','source']},
                'scene':{'type':'string','enum':['mascot','form','scroll']},
                'workspace':{'type':'string','description':'用户实际工作区的绝对路径，须为已有目录。'},
                'name':{'type':'string','description':'输出文件名前缀，英文小写字母、数字和连字符，不含扩展名。'},
                'title':{'type':'string','maxLength':80,'description':'作品中文标题。'},
                'description':{'type':'string','maxLength':600,'description':'作品的中文说明。'},
            },'required':['action'],'additionalProperties':False,
        }, parallel_safe=False))
    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_runtime.execute, inputs)
    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
