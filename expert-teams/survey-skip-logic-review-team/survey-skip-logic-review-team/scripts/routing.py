"""离线分析单选问卷的跳题路径。"""
import hashlib
from io import TextIOWrapper
import json
from collections import deque
from pathlib import Path
import re
import sys

END = 'END'
FILES = {'baseline': 'baseline.json', 'analyze': 'analysis.json', 'verify': 'verification.json'}
MAX_INPUT = 128 * 1024


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('JSON 对象中有重复键。')
        result[key] = value
    return result


def question_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,31}', value)


def load_spec(path):
    if not path.is_file():
        raise ValueError('输入必须是本地 JSON 文件。')
    with path.open('rb') as stream:
        raw = stream.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError('输入超出 128 KiB。')
    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)
    if not isinstance(data, dict) or set(data) != {'start', 'questions'}:
        raise ValueError('根对象必须仅包含 start 和 questions。')
    start, graph = data['start'], data['questions']
    if not isinstance(graph, dict) or not 1 <= len(graph) <= 120:
        raise ValueError('questions 必须是包含 1 至 120 道题的对象。')
    for q, choices in graph.items():
        if not question_id(q) or q == END:
            raise ValueError('题目编号不合法，或使用了保留值 END。')
        if not isinstance(choices, dict) or not 1 <= len(choices) <= 12:
            raise ValueError(f'题目 {q} 必须声明 1 至 12 个单选选项。')
        for option, target in choices.items():
            if not re.fullmatch(r'[\w-]{1,32}', option) or not question_id(target):
                raise ValueError(f'题目 {q} 的选项名称或跳转目标不合法。')
    if not question_id(start) or start not in graph:
        raise ValueError('start 必须指向已定义的题目。')
    return start, graph, hashlib.sha256(raw).hexdigest()


def paths_from(graph, start):
    """正向广度遍历，返回到各可达题的最短选项序列。"""
    paths = {start: []}
    todo = deque([start])
    while todo:
        source = todo.popleft()
        for option, target in sorted(graph[source].items()):
            if target in graph and target not in paths:
                paths[target] = paths[source] + [option]
                todo.append(target)
    return paths


def analyze(start, graph):
    paths = paths_from(graph, start)
    broken, loops = [], []
    for question in sorted(paths):
        for option, target in sorted(graph[question].items()):
            if target != END and target not in graph:
                broken.append([question, option, target, paths[question] + [option]])
        for option, target in sorted(graph[question].items()):
            if target not in graph:
                continue
            back = paths_from(graph, target).get(question)
            if back is not None:
                loops.append([question, paths[question], [option, *back]])
                break
    return {'unreachable': sorted(graph.keys() - paths.keys()), 'broken': broken, 'loops': loops}


def independent(start, graph):
    """逐轮扩展直接后继的传递闭包，不使用正向路径或分析产物。"""
    closure = {q: set(choices.values()) & graph.keys() for q, choices in graph.items()}
    changed = True
    while changed:
        changed = False
        for q, destinations in closure.items():
            larger = destinations.union(*(closure[n] for n in destinations))
            if larger != destinations:
                closure[q] = larger
                changed = True
    reachable = {start} | closure[start]
    return {
        'unreachable': sorted(graph.keys() - reachable),
        'broken': [[q, a, t] for q in sorted(reachable) for a, t in sorted(graph[q].items())
                   if t != END and t not in graph],
        'loops': sorted(q for q in reachable if q in closure[q]),
    }


def replay(graph, start, options):
    if not isinstance(options, list) or len(options) > len(graph):
        raise ValueError('证据路径长度无效。')
    for option in options:
        if not isinstance(option, str) or option not in graph.get(start, {}):
            raise ValueError('证据路径中的选项无法执行。')
        start = graph[start][option]
    return start


def compare(start, graph, analysis, baseline):
    if set(analysis) != {'unreachable', 'broken', 'loops'} or analysis['unreachable'] != baseline['unreachable']:
        raise ValueError('不可达题目的分析结果与独立核验不一致。')
    if not isinstance(analysis['broken'], list) or not isinstance(analysis['loops'], list):
        raise ValueError('分析证据结构不合法。')
    broken_keys, loop_keys = [], []
    for question, option, target, path in analysis['broken']:
        if not isinstance(path, list) or not path or path[-1] != option or (
            replay(graph, start, path[:-1]) != question or replay(graph, start, path) != target
        ):
            raise ValueError('断链证据路径回放不一致。')
        broken_keys.append([question, option, target])
    for question, prefix, lap in analysis['loops']:
        if not lap or replay(graph, start, prefix) != question or replay(graph, question, lap) != question:
            raise ValueError('循环证据路径回放不一致。')
        loop_keys.append(question)
    if broken_keys != baseline['broken'] or loop_keys != baseline['loops']:
        raise ValueError('断链或循环清单与独立核验不一致。')


def write_new(path, content):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)


def store(path, digest, value):
    write_new(path, json.dumps({'source_sha256': digest, 'result': value}, ensure_ascii=False, indent=2) + '\n')


def read(path, digest):
    content = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)
    if content['source_sha256'] != digest:
        raise ValueError('输入在交接后发生变化；请使用新的输出目录重新运行。')
    return content['result']


def report_text(start, digest, result):
    def sequence(path):
        return ' → '.join(f'`{option}`' for option in path) or '（起始题）'

    lines = ['# 问卷跳题逻辑核验报告', '', f'起始题：`{start}`', f'输入 SHA-256：`{digest}`', '',
             '核验状态：独立清单与路径回放一致。', '']
    if not any(result.values()):
        lines.extend(['未发现结构性缺陷。', ''])
    lines += ['## 不可达题目', '']
    lines.extend([f'- `{q}`' for q in result['unreachable']] or ['无。'])
    lines += ['', '## 可达断链', '']
    lines.extend([f'- `{q}` 的选项 `{option}` 指向未定义题目 `{target}`；从起始题作答：{sequence(path)}。'
                  for q, option, target, path in result['broken']] or ['无。'])
    lines += ['', '## 可达循环', '']
    lines.extend([f'- 到达 `{q}`：{sequence(prefix)}；再选 {sequence(lap)} 返回同一题。'
                  for q, prefix, lap in result['loops']] or ['无。'])
    lines += ['', '循环表示存在可重复选择，不表示所有作答都会困在循环中。',
              '仅核验声明的单选跳转；不验证题目措辞、业务意图或线上配置。不可达题的内部跳转未做路径核验。', '']
    return '\n'.join(lines)


def run(step, source, out):
    if not out.is_dir():
        raise ValueError('输出目录不存在；请显式创建本次专用的空目录。')
    start, graph, digest = load_spec(source)
    if step == 'validate':
        if next(out.iterdir(), None) is not None:
            raise ValueError('输出目录非空；请使用本次专用的空目录。')
    elif step == 'baseline':
        store(out / FILES[step], digest, independent(start, graph))
    elif step == 'analyze':
        try:
            # Check the handoff envelope; the independent findings never enter the search.
            read(out / FILES['baseline'], digest)
        except FileNotFoundError as exc:
            raise ValueError('尚未生成独立基线；请先等待核验员成功完成基线任务。') from exc
        store(out / FILES[step], digest, analyze(start, graph))
    else:
        baseline = read(out / FILES['baseline'], digest)
        analysis = read(out / FILES['analyze'], digest)
        if baseline != independent(start, graph):
            raise ValueError('独立基线与原始输入不一致。')
        compare(start, graph, analysis, baseline)
        seal = hashlib.sha256(json.dumps(analysis, sort_keys=True).encode('utf-8')).hexdigest()
        if step == 'verify':
            store(out / FILES[step], digest, {'analysis_sha256': seal})
        else:
            if read(out / FILES['verify'], digest) != {'analysis_sha256': seal}:
                raise ValueError('已核验的分析内容发生变化。')
            write_new(out / '报告.md', report_text(start, digest, analysis))


def main(args):
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding='utf-8')
    if args in (['--help'], ['-h']):
        print('用法：python routing.py validate|baseline|analyze|verify|report 输入.json 输出目录')
        return 0
    if len(args) != 3 or args[0] not in ('validate', *FILES, 'report'):
        print('参数错误；使用 --help 查看用法。', file=sys.stderr)
        return 2
    step, source, out = args
    try:
        run(step, Path(source), Path(out))
    except (json.JSONDecodeError, UnicodeError, RecursionError):
        print('无法处理 JSON：请检查 UTF-8 编码、格式及嵌套层级。', file=sys.stderr)
    except FileExistsError:
        print('结果文件已存在，不会覆盖。请使用新的输出目录。', file=sys.stderr)
    except OSError:
        print('无法读取输入、读取所需交接文件或写入输出目录。', file=sys.stderr)
    except (ValueError, KeyError, TypeError):
        error = sys.exc_info()[1]
        message = str(error) if type(error) is ValueError and re.search(r'[\u4e00-\u9fff]', str(error)) else '输入或交接文件结构不合法。'
        print(message, file=sys.stderr)
    else:
        print({'validate': '输入校验通过；未写入文件。',
               'baseline': '独立基线已保存。', 'analyze': '正向分析已保存。',
               'verify': '独立核验通过。', 'report': '已生成报告.md。'}[step])
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
