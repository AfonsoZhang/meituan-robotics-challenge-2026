#!/usr/bin/env python3
"""Rebuild the technical report PDF from Markdown, Mermaid, original CAD and TeX.

Local export only; never invokes a robot or changes report facts. Written with
OpenAI Codex. External dependencies and reproducible commands are in README.md.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import subprocess
from urllib.parse import unquote, urlsplit
import markdown
from bs4 import BeautifulSoup
from weasyprint import HTML
from render_diagrams import render as render_diagram

ROOT = Path(__file__).resolve().parents[2]

CSS = r"""
@page { size: A4; margin: 20mm;
 @top-left { content: 'AUBO S3 电池搬运技术方案'; font: 8pt 'Microsoft YaHei'; color: #666666; }
 @top-right { content: '技术报告'; font: 8pt 'Microsoft YaHei'; color: #666666; }
 @bottom-center { content: counter(page) ' / ' counter(pages); font: 8pt 'Microsoft YaHei'; color: #666666; }
}
@page:first { @top-left { content: none; } @top-right { content: none; } }
html { font-family: 'Report Body', 'SimSun', 'Microsoft YaHei', serif; font-size: 10.5pt; color: #161616; }
body { margin: 0; line-height: 1.55; }
p { margin: 0 0 2.8mm; text-align: justify; orphans: 3; widows: 3; }
a { color: inherit; text-decoration: none; overflow-wrap: anywhere; }
strong { font-family: 'Microsoft YaHei', sans-serif; font-weight: 700; }
h1, h2, h3 { font-family: 'Microsoft YaHei', sans-serif; color: #111111; line-height: 1.35; break-after: avoid; }
h1 { font-size: 22pt; margin: 0 0 12mm; font-weight: 700; bookmark-level: none; }
h2 { font-size: 15pt; margin: 7mm 0 4mm; bookmark-level: 1; }
h3 { font-size: 11.5pt; margin: 5mm 0 3mm; bookmark-level: 2; }
blockquote { margin: 5mm 0; padding: 3mm 0; font-size: 9.5pt; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; margin: 3mm 0 5mm; border-top: .8pt solid #222222; border-bottom: .8pt solid #222222; font-size: 8.8pt; line-height: 1.5; }
thead { display: table-header-group; }
th { font-family: 'Microsoft YaHei', sans-serif; background: white; font-weight: 700; color: #111111; border-bottom: .5pt solid #444444; }
th, td { box-sizing: border-box; text-align: left; vertical-align: top; padding: 2.1mm 2mm; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
td p { margin: 0; }
code { font-family: 'DejaVu Sans Mono', 'Microsoft YaHei', monospace; font-size: .88em; overflow-wrap: anywhere; }
pre { padding: 3mm; background: #F5F5F5; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 9pt; }
figure { margin: 4mm 0; break-inside: avoid; text-align: center; }
figure img { display: block; max-width: 100%; max-height: 225mm; margin: 0 auto; }
figure.diagram img { width: 100%; height: auto; max-height: 215mm; }
figure.cad img { width: 170mm; height: 192mm; }
figcaption { margin: 2.2mm 0 0; font-size: 9pt; color: #444444; text-align: left; line-height: 1.4; }
.math-block { text-align: center; margin: 3mm 0 4mm; break-inside: avoid; }
.math-block img { max-width: 100%; }
.math-inline { display: inline-block; vertical-align: middle; margin: 0 1px; }
.cover { height: 252mm; box-sizing: border-box; page-break-after: always; padding-top: 31mm; text-align: center; }
.cover .eyebrow { font-size: 10pt; color: #444444; margin: 0 0 16mm; padding-top: 5mm; }
.cover .subtitle { font-size: 12pt; line-height: 1.7; color: #333333; margin-bottom: 20mm; text-align: center; }
.cover .meta { font-size: 10pt; line-height: 2; text-align: center; }
.cover blockquote { margin-top: 22mm; background: white; }
.contents { page-break-after: always; }
.contents h2 { bookmark-level: none; margin-top: 0; }
.contents a { display: block; margin: 3mm 0; color: #222222; }
.contents a.level-3 { margin: 1.8mm 0 1.8mm 6mm; font-size: 9.5pt; color: #444444; }
.contents a::after { content: leader('.') target-counter(attr(href), page); }
.body-start { margin-top: 0; }
.figure-section { break-before: page; margin-top: 0; }
.source-note { font-size: 8.3pt; color: #555555; line-height: 1.4; margin-top: -1mm; margin-bottom: 3mm; }
.has-source-note { break-after: avoid; }
"""


def run(command):
    subprocess.run([str(x) for x in command], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT/'docs/技术报告.md')
    p.add_argument('--node-modules', type=Path, default=ROOT/'tools/report/node_modules')
    p.add_argument('--body-font', type=Path, help='Local SimSun font file; auto-detected when omitted')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    source = args.source.resolve()
    output = args.output or source.with_suffix('.pdf')
    assets = ROOT/'docs/assets/report-v0.4'
    assets.mkdir(parents=True, exist_ok=True)
    build = ROOT/'outputs/report-v0.4'
    build.mkdir(parents=True, exist_ok=True)
    modules = args.node_modules.resolve()
    font_candidates = [args.body_font] if args.body_font else [
        Path.home()/'.local/share/fonts/simsun.ttc', Path('/mnt/c/Windows/Fonts/simsun.ttc')]
    body_font = next((path.resolve() for path in font_candidates if path.is_file()), None)
    if args.body_font and body_font is None:
        p.error('--body-font must name an existing font file')
    font_css = (f"@font-face {{ font-family: 'Report Body'; src: url('{body_font.as_uri()}'); }}\n"
                if body_font else '')
    text = source.read_text()
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    names = ['system-architecture','task-flow','pickplace-flow']
    captions = ['系统总体架构。',
                'Task 主流程及逐件循环。异常与控制状态单列，分支未展开。',
                'PickPlace 抓放流程及异常处理。']
    diagram_index = 0
    diagram_checks = {}

    def diagram(match):
        nonlocal diagram_index
        idx = diagram_index; diagram_index += 1
        name = names[idx]; body = match.group(1)
        mmd = assets/f'{name}.mmd'
        svg = assets/f'{name}.svg'
        mmd.write_text(body)
        diagram_checks[name] = render_diagram(body, name, svg)
        return f'\n<figure class="diagram" id="{name}"><img src="{svg.as_uri()}" alt="{captions[idx]}"><figcaption>图 {idx+1}　{captions[idx]}</figcaption></figure>\n'

    text = re.sub(r'```mermaid\n(.*?)```', diagram, text, flags=re.S)
    assert diagram_index==3, 'Expected the three report diagrams'
    formulas=[]
    def formula(match):
        block = match.group(1) is not None
        tex = (match.group(1) if block else match.group(2)).strip()
        idx=len(formulas); path=assets/f'math-{idx:02}.svg'
        formulas.append({'tex':tex,'display':block,'path':str(path)})
        return f'<span data-formula="{idx}"></span>' if not block else f'\n<div data-formula="{idx}"></div>\n'
    text=re.sub(r'\$\$(.*?)\$\$|(?<!\$)\$([^\n$]+)\$(?!\$)',formula,text,flags=re.S)
    (build/'math.json').write_text(json.dumps(formulas))
    run(['node',ROOT/'tools/report/math_to_svg.cjs',modules,build/'math.json'])
    rendered=markdown.markdown(text,extensions=['fenced_code','tables','toc'],extension_configs={'toc':{'toc_depth':'2-3'}})
    soup=BeautifulSoup(rendered,'html.parser')
    for paragraph in soup.find_all('p'):
        if paragraph.get_text().startswith('来源：'):
            paragraph['class']='source-note'
            previous=paragraph.find_previous_sibling('p')
            if previous: previous['class']='has-source-note'
    for heading in soup.find_all('h3'):
        if heading.get_text().startswith('3.3 '): heading['class']='figure-section'
    for placeholder in soup.select('[data-formula]'):
        entry=formulas[int(placeholder['data-formula'])]
        svg=BeautifulSoup(Path(entry['path']).read_text(),'xml').svg
        # MathJax uses 1000 SVG units per em; apply the body font size in pt.
        view=list(map(float,svg['viewBox'].split()))
        size=11.5 if entry['display'] else 10.5
        image=soup.new_tag('img',src=Path(entry['path']).as_uri(),alt=entry['tex'])
        image['style']=f'width:{view[2]/1000*size:.3f}pt;height:{view[3]/1000*size:.3f}pt;'
        placeholder['class']='math-block' if entry['display'] else 'math-inline'
        placeholder.append(image)
        del placeholder['data-formula']
    for image in soup.find_all('img'):
        src=image['src']
        if not urlsplit(src).scheme:
            image['src']=(source.parent/unquote(src)).resolve().as_uri()
        if 'v1-cad-views.svg' in src:
            parent=image.parent
            figure=soup.new_tag('figure',attrs={'class':'cad'})
            image.extract();figure.append(image)
            caption=soup.new_tag('figcaption')
            caption.string='图 4　舌规削平前 CAD 四视图。'
            figure.append(caption);parent.replace_with(figure)
    for table in soup.find_all('table'):
        count=len(table.find('tr').find_all('th'))
        table['class']=f'cols-{count}'
        widths=[19,38,43] if count==3 else [19,81] if count==2 else [100/count]*count
        columns=soup.new_tag('colgroup')
        for width in widths: columns.append(soup.new_tag('col',style=f'width:{width}%'))
        table.insert(0,columns)
    for code in soup.find_all('code'):
        if code.parent.name=='pre':continue
        value=code.get_text();code.clear()
        for token in re.split(r'([A-Za-z0-9_./@-]{16,})',value):
            if re.fullmatch(r'[A-Za-z0-9_./@-]{16,}',token):
                for chunk in re.findall(r'.{1,14}',token):
                    code.append(chunk);code.append(soup.new_tag('wbr'))
            else:code.append(token)
    # Preserve local evidence references. Do not manufacture GitHub links for
    # unpublished working files; the user requested no GitHub links in the PDF.
    for anchor in soup.find_all('a',href=True):
        href=anchor['href']
        if not urlsplit(href).scheme and not href.startswith('#'):
            target=(source.parent/unquote(href.split('#')[0])).resolve()
            assert target.is_file(), target
            anchor['href']=target.as_uri()
            if '#' in href:anchor['href']+='#'+href.split('#',1)[1]
    title=soup.h1.extract()
    subtitle=soup.find('p').extract();subtitle['class']='subtitle'
    meta=soup.find('p').extract();meta['class']='meta'
    note=soup.find('blockquote')
    if note: note.extract()
    cover=soup.new_tag('section',attrs={'class':'cover'})
    eyebrow=soup.new_tag('div',attrs={'class':'eyebrow'});eyebrow.string='技术方案报告  /  2026'
    for node in [eyebrow,title,subtitle,meta]:cover.append(node)
    if note: cover.append(note)
    contents=soup.new_tag('nav',attrs={'class':'contents'})
    heading=soup.new_tag('h2');heading.string='目录';contents.append(heading)
    for heading in soup.find_all(['h2','h3']):
        link=soup.new_tag('a',href='#'+heading['id'],attrs={'class':f'level-{heading.name[1]}'})
        link.string=heading.get_text();contents.append(link)
    soup.h2['class']='body-start'
    soup.insert(0,contents);soup.insert(0,cover)
    html_doc='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>'+html.escape(title.get_text())+'</title><meta name="generator" content="Local Markdown / Mermaid / MathJax / WeasyPrint export"><style>'+font_css+CSS+'</style></head><body>'+str(soup)+'</body></html>'
    (build/'report.html').write_text(html_doc)
    HTML(string=html_doc,base_url=str(source.parent)).write_pdf(str(output))
    (assets/'report-export.json').write_text(json.dumps({
        'source':str(source.relative_to(ROOT)), 'source_sha256':original_hash,
        'pdf':str(output.relative_to(ROOT)), 'pdf_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'diagrams':diagram_checks, 'formulas':len(formulas), 'page':'A4','margins_mm':20,
        'font':'SimSun' if body_font else 'Microsoft YaHei','font_pt':10.5,
        'heading_font':'Microsoft YaHei',
        'visual_style':'Black/gray typography, white three-rule tables, neutral flow diagrams; original CAD colors preserved',
        'source_content':'No formula, dimension, TCP value, transition condition or test metric changed by export',
    },ensure_ascii=False,indent=2)+'\n')
    print(output)


if __name__=='__main__':main()
