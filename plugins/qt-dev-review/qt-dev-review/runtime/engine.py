from .common import *
import importlib.util,sys,html
HERE=Path(__file__).resolve().parents[1]
MODULES={}
def load(kind):
 if kind in MODULES:return MODULES[kind]
 name='qt_port_'+kind
 s=importlib.util.spec_from_file_location(name,HERE/'vendor'/('qt_qml_lint.py' if kind=='qml' else 'qt_review_lint.py'))
 m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);MODULES[kind]=m;return m
ADVICE={'DEP':'检查旧式 Qt API 与标准 C++ 替代方案，确认目标 Qt 版本兼容性。','HDR':'检查公共头文件依赖、声明和命名空间边界。','INC':'检查头文件包含顺序及直接依赖。','PAT':'检查该处 C++ 写法、容器操作和性能陷阱。','LCY':'检查 QObject 所有权、父子关系和信号连接的生命周期。','ERR':'检查错误值、异常分支和异步请求失败处理。','MDL':'检查模型变更通知、角色名称与 begin/end 配对。','BND':'检查 QML 属性类型、绑定依赖和空值保护。','LAY':'检查布局约束、锚点冲突和尺寸计算。','DEL':'检查委托的状态复用、作用域和必要属性。','STA':'检查状态切换、条件分支及绑定恢复。','STY':'检查主题、颜色和样式声明的一致性。','LDR':'检查 Loader 的装载时机和对象访问安全。','IMG':'检查图片加载及 sourceSize 等资源约束。','ORD':'检查 QML 成员声明顺序。','VAR':'检查类型推导和变量初始化。','VAL':'检查值语义及不必要复制。','API':'检查 API 参数和命名语义。','TRN':'检查类型转换及隐式布尔转换。','TMO':'检查超时类型、时间单位与边界。','ENM':'检查枚举与布尔标志的可读性。'}
def execute(q):
 root=workspace(q)
 if q.get('action')!='review':raise InputError('仅支持 review 审校操作。')
 files=q.get('files')
 if not isinstance(files,list) or not 1<=len(files)<=20:raise InputError('请选择1至20个 C++ 或 QML 文件。')
 out=safe(root,q.get('report_file','qt-review.md'))
 if out.suffix!='.md':raise InputError('审校报告必须使用 .md 扩展名。')
 sources=[]
 for rel in files:
  f=safe(root,rel)
  if f.suffix not in ('.qml','.cpp','.h','.hpp','.cc','.cxx'):raise InputError('仅支持 QML 和 C++ 源文件。')
  text=read(f);sources.append((rel,f,text))
 if out in [f for _,f,_ in sources]:raise InputError('报告不能覆盖源文件。')
 findings=[]
 for rel,f,text in sources:
  for x in load('qml' if f.suffix=='.qml' else 'cpp').scan_file(str(f)):
   exact={'STY-1':'根组件建议声明 id: root，确保属性查找有明确作用域。','BND-1':'property var 可改为具体属性类型；先确认值的实际类型和绑定需求。','DEP-1':'检查是否可以用 std::unique_ptr 替代 QScopedPointer；确认所有权和目标 Qt/C++ 版本。'}
   findings.append({'file':rel,'line':x.line,'rule':x.rule,'message':exact.get(x.rule,ADVICE.get(x.rule.split('-')[0],'检查该规则对应的代码上下文，并核对目标 Qt 版本。')),'context':text.splitlines()[max(0,x.line-1)] if 0<x.line<=len(text.splitlines()) else ''})
 lines=['# Qt 开发审校报告','',f'已扫描 {len(sources)} 个文件，发现 {len(findings)} 个待核实项。','启发式规则可能误报；未执行编译、Qt GUI 或性能测试。','']
 for x in findings:lines += [f"## {x['file']}:{x['line']} · {x['rule']}",x['message'],'```',x['context'].replace('```','｀｀｀'),'```','']
 atomic(out,'\n'.join(lines))
 return {'ok':True,'message':'中文审校报告已生成；代码未修改。','scanned':len(sources),'count':len(findings),'findings':findings[:100],'truncated':len(findings)>100,'report':str(out)}
