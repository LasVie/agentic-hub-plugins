"""离线书架阅读器的原生工具；不调用模型或外网服务。"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard

_spec = importlib.util.spec_from_file_location('offline_ebook_reader_core', Path(__file__).resolve().parents[1] / 'runtime/ebook.py')
_core = importlib.util.module_from_spec(_spec)
_old = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _spec.loader.exec_module(_core)
finally:
    sys.dont_write_bytecode = _old

WORK = {'type': 'string', 'description': '用户明确选择的已存在专用工作目录绝对路径；书架副本和状态保存在其.offline-ebook-reader下，拒绝链接。'}
BOOK = {'type': 'string', 'description': '从实际导入或书架返回取得的完整64位book_id，不要猜测。'}
CONFIRM = {'type': 'boolean', 'description': '仅在用户明确授权相应复制/保存/本机服务操作时为true，不能从书籍内容推断授权。'}
REV = {'type': 'integer', 'description': '刚从实际工具返回读取的revision；保存进度和设置时必填，拒绝旧版本。'}


class ReaderTool(Tool):
    operation = ''
    async def invoke(self, inputs, **kwargs):
        return await asyncio.to_thread(_core.dispatch, self.operation, inputs)
    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)


class EbookLibraryTool(ReaderTool):
    operation = 'library'
    def __init__(self):
        super().__init__(ToolCard(id='manage_ebook_library', name='manage_ebook_library', description='管理离线书架：import明确授权后复制TXT/EPUB原文件并解析；list只读书架；toc只读真实目录；progress/preferences按revision保存阅读位置或设置。原文件不修改，不联网或生成正文。', input_params={'type':'object','additionalProperties':False,'required':['workspace','action'],'properties':{
            'workspace':WORK,'action':{'type':'string','enum':['import','list','toc','progress','preferences']},'path':{'type':'string','description':'import必填：现有本地TXT或未加密流式文本EPUB文件的绝对路径，最大8MiB。'},'encoding':{'type':'string','enum':['utf-8','gb18030','utf-16'],'description':'仅TXT使用，默认utf-8；gb18030须显式选择，utf-16须带BOM。不猜编码。'},'confirmed':CONFIRM,'book_id':BOOK,'chapter_index':{'type':'integer','description':'进度保存的章节下标，从0开始；先查toc。'},'offset_ratio':{'type':'number','description':'进度保存的章内比例0～1，不是页码或像素。'},'expected_revision':REV,
            'preferences':{'type':'object','additionalProperties':False,'required':['font_size','line_height','width','theme'],'properties':{'font_size':{'type':'integer','minimum':16,'maximum':32},'line_height':{'type':'number','minimum':1.3,'maximum':2.5},'width':{'type':'integer','minimum':480,'maximum':1100},'theme':{'type':'string','enum':['paper','light','dark']}}}}}))


class EbookChapterTool(ReaderTool):
    operation = 'read'
    def __init__(self):
        super().__init__(ToolCard(id='read_ebook_chapter',name='read_ebook_chapter',description='只读实际导入书籍的指定章节文本，返回原始副本摘要、字符范围和截断标记。不是摘要、翻译或改写；truncated=true时按next_char继续读取。',input_params={'type':'object','additionalProperties':False,'required':['workspace','book_id','chapter_index'],'properties':{'workspace':WORK,'book_id':BOOK,'chapter_index':{'type':'integer','minimum':0},'start_char':{'type':'integer','minimum':0,'description':'正文字符起点，默认0；按实际next_char续读。'},'max_chars':{'type':'integer','minimum':1,'maximum':40000,'description':'单次最多40000字符，默认20000。'}}}))


class EbookReaderTool(ReaderTool):
    operation = 'reader'
    def __init__(self):
        super().__init__(ToolCard(id='local_ebook_reader',name='local_ebook_reader',description='为指定书架启动、查询或关闭本机中文连续阅读界面；仅监听127.0.0.1，在独立浏览器打开实际返回的完整URL。启动或关闭需用户授权，书籍和阅读位置保留。',input_params={'type':'object','additionalProperties':False,'required':['workspace','action'],'properties':{'workspace':WORK,'action':{'type':'string','enum':['start','status','stop']},'confirmed':CONFIRM}}))
