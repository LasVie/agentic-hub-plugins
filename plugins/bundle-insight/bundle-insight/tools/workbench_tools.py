"""前端包体积透视台的两个原生WorkSwarm工具。"""
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard
spec=importlib.util.spec_from_file_location("bundle_insight_runtime",Path(__file__).resolve().parents[1]/"runtime/launcher.py")
runtime=importlib.util.module_from_spec(spec);sys.modules[spec.name]=runtime;spec.loader.exec_module(runtime)
COMMON={"workspace":{"type":"string","description":"用户选择的已存在专用工作目录绝对路径；插件只在其.bundle-insight子目录保存数据。"},"confirmed":{"type":"boolean","description":"用户明确授权启动、关闭、执行或写入后设为true。"}}
class WorkbenchTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id="bundle_insight_workbench",name="bundle_insight_workbench",description="为前端包体积透视台启动、查询或关闭专用本机中文工作台。返回真实访问地址；不修改宿主或其他插件。",input_params={"type":"object","required":["workspace","action"],"additionalProperties":False,"properties":{**COMMON,"action":{"type":"string","enum":["start","status","stop"]}}}))
 async def invoke(self,inputs,**kwargs):return await runtime.invoke(inputs)
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
class EngineTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id="bundle_insight_operate",name="bundle_insight_operate",description="调用前端包体积透视台的真实引擎操作。工作台需先启动。operation和arguments见本插件Skill；依据实际ok/result答复，不能猜测执行结果。",input_params={"type":"object","required":["workspace","operation","arguments","confirmed"],"additionalProperties":False,"properties":{**COMMON,"operation":{"type":"string","description":"本插件Skill列出的操作名称"},"arguments":{"type":"object","description":"操作参数对象；不得传入不受支持的宿主命令"}}}))
 async def invoke(self,inputs,**kwargs):return runtime.compact_result(await runtime.invoke({"workspace":inputs.get("workspace"),"confirmed":inputs.get("confirmed"),"action":"operate","params":{**inputs.get("arguments",{}),"op":inputs.get("operation")}}))
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
