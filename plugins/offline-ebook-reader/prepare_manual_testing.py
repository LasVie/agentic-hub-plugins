"""Create original Chinese synthetic books in a NEW directory; never overwrite."""
import io
import json
from pathlib import Path
import sys
import zipfile


def epub_bytes(*, version='3.0', fixed=False, encrypted=False, missing=False, image=False, unsafe=False):
    opf = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="{version}"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>中文离线阅读示例</dc:title><dc:creator>本地原创测试</dc:creator>{'<meta property="rendition:layout">pre-paginated</meta>' if fixed else ''}</metadata><manifest><item id="two" href="later.xhtml" media-type="application/xhtml+xml"/><item id="one" href="first.xhtml" media-type="application/xhtml+xml"/><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest><spine><itemref idref="one"/><itemref idref="two"/></spine></package>'''
    paras = '\n'.join(f'<p>第{i}段：这是一份原创合成中文测试材料，用来检查连续滚动、阅读位置和重开恢复。春天的山坡有风，路边的小屋亮着灯。</p>' for i in range(1,81))
    page = lambda title, text: f'<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{title}</title></head><body><h1>{title}</h1>{text}</body></html>'
    b = io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/epub+zip')
        z.writestr('META-INF/container.xml','<container><rootfiles><rootfile full-path="OEBPS/book.opf"/></rootfiles></container>')
        z.writestr('OEBPS/book.opf',opf)
        z.writestr('OEBPS/nav.xhtml',page('目录','<nav><a href="first.xhtml">第一章 出发</a><a href="later.xhtml">第二章 归来</a></nav>'))
        if not missing:
            z.writestr('OEBPS/first.xhtml',page('出发',paras + '<img src="https://example.invalid/never-load.png" alt="远方的小屋"/><script>window.shouldNeverRun=true</script>') if not image else '<html><body><img src="image.png"/></body></html>')
        z.writestr('OEBPS/later.xhtml',page('归来',paras.replace('春天','秋天')))
        if encrypted: z.writestr('META-INF/encryption.xml','<encryption/>')
        if unsafe: z.writestr('../escape.txt','不应导出')
    return b.getvalue()


def main(directory):
    root = Path(directory)
    root.mkdir(parents=True,exist_ok=False)
    (root/'书架工作目录').mkdir()
    paragraphs='\n\n'.join(f'第{i}段：这是原创合成测试文本。中文、标点与表情🙂保持可读；请滚动并保存位置，刷新后核对。' for i in range(1,101))
    text='第一章 清晨\n'+paragraphs+'\n第二章 午后\n'+paragraphs+'\n第三章 夜晚\n'+paragraphs
    (root/'中文三章示例.txt').write_text(text,encoding='utf-8')
    (root/'旧编码示例.txt').write_bytes('第一章 旧编码\n这份中文示例使用GB18030，须显式选择编码。'.encode('gb18030'))
    (root/'中文顺序示例.epub').write_bytes(epub_bytes())
    (root/'固定版式拒绝.epub').write_bytes(epub_bytes(fixed=True))
    (root/'损坏示例.epub').write_bytes(b'PK-not-an-epub')
    print(json.dumps({'inputs':str(root.resolve()),'workspace':str((root/'书架工作目录').resolve()),'fixtures':'Original synthetic text only; no third-party books.'},ensure_ascii=False,indent=2))


if __name__=='__main__': main(sys.argv[1])
