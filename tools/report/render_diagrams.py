"""Fixed print layouts for the report's three Mermaid graphs.

Labels and relationships are read from Markdown. Every drawn edge is matched
against the parsed graph; unhandled nodes or edges fail the export. Layout is
presentation only. Written with OpenAI Codex; no generated raster imagery.
"""
import html
import re
from collections import Counter
from pathlib import Path

NODE = r'([A-Z][A-Z_0-9]*)\s*(\(\[.*?\]\)|\[.*?\]|\{.*?\})'
EDGE = r'([A-Z][A-Z_0-9]*)(?:\(\[.*?\]\)|\[.*?\]|\{.*?\})?\s*(-->|-\.\s*(.*?)\s*\.->)(?:\|([^|]*)\|)?\s*([A-Z][A-Z_0-9]*)'


def parse(source):
    nodes, shapes, edges = {}, {}, []
    for line in source.splitlines():
        line = line.strip()
        if line.startswith(('subgraph ', 'class', '%%')):
            continue
        for key, body in re.findall(NODE, line):
            shapes[key] = 'diamond' if body.startswith('{') else 'round' if body.startswith('([') else 'rect'
            label = body[2:-2] if body.startswith('([') else body[1:-1]
            nodes[key] = label.strip('"').replace('<br/>', '\n')
        m = re.search(EDGE, line)
        if m:
            a, arrow, dashed_label, label, b = m.groups()
            edges.append((a, b, label or dashed_label or '', arrow != '-->'))
    return nodes, shapes, edges


class Drawing:
    def __init__(self, source, width, height):
        self.nodes, self.shapes, self.expected = parse(source)
        self.done = []
        self.positions = {}
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="170mm" height="{170*height/width:.3f}mm" viewBox="0 0 {width} {height}">',
                      '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#444444"/></marker></defs>',
                      f'<rect width="{width}" height="{height}" fill="white"/>']

    def text(self, x, y, text, size=13, anchor='middle', bold=False):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{y+i*(size+3):.2f}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="#161616">{html.escape(line)}</text>')

    def edge(self, a, b, path, label_xy=None, label=None, anchor='middle'):
        candidates = [e for e in self.expected if e[:2] == (a, b)]
        assert len(candidates) == 1, (a,b,candidates)
        edge = candidates[0]; self.done.append(edge)
        self.parts.append(f'<g data-edge="{a}-{b}"><path d="{path}" fill="none" stroke="#444444" stroke-width="1.2" marker-end="url(#arrow)"'+(' stroke-dasharray="5 3"' if edge[3] else '')+'/></g>')
        if edge[2]:
            assert label_xy is not None, edge
            display = label or edge[2]
            assert re.sub(r'\s','',display)==re.sub(r'\s','',edge[2])
            self.text(*label_xy, display, size=11.5, anchor=anchor)

    def node(self, key, x, y, width, height, label=None):
        self.positions[key] = (x, y, width, height)
        display = label or self.nodes[key]
        assert re.sub(r'\s','',display)==re.sub(r'\s','',self.nodes[key]), key
        shape = self.shapes[key]
        fill,stroke = '#FFFFFF','#444444'
        if key in ('R','RC','FAIL','FAULT','S','FINISHED','RECOVERY','TASK_FAILED','CANCEL_PENDING','CANCELLED'):
            fill,stroke='#F3F3F3','#444444'
        self.parts.append(f'<g data-node="{key}">')
        if shape=='diamond':
            self.parts.append(f'<path d="M{x} {y-height/2} L{x+width/2} {y} L{x} {y+height/2} L{x-width/2} {y} Z" fill="{fill}" stroke="{stroke}"/>')
        else:
            radius=height/2 if shape=='round' else 0
            self.parts.append(f'<rect x="{x-width/2}" y="{y-height/2}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')
        lines=display.split('\n'); y0=y-(len(lines)-1)*8+4
        for i,line in enumerate(lines):
            self.text(x,y0+i*16,line,size=11.5 if re.search('[A-Z_]{3}',line) else 13)
        self.parts.append('</g>')

    def save(self, path):
        assert set(self.positions)==set(self.nodes), (set(self.positions)^set(self.nodes))
        assert Counter(self.done)==Counter(self.expected), (Counter(self.done)-Counter(self.expected),Counter(self.expected)-Counter(self.done))
        self.parts.append('</svg>')
        Path(path).write_text('\n'.join(self.parts))
        return {'nodes':len(self.nodes),'edges':len(self.done),'width_mm':170,'semantics_checked':True}


def render(source, name, path):
    if name=='pickplace-flow':
        d=Drawing(source,650,790)
        d.text(152,18,'正常抓放流程',bold=True)
        d.text(470,250,'异常处理',bold=True)
        yy=dict(A=45,B=100,C=165,D=230,E=295,F=360,G=418,H=483,I=548,J=606,K=671,S=736)
        hh={k:(58 if k in 'CEHK' else 35) for k in yy}
        order=list(yy)
        for a,b in zip(order,order[1:]):
            d.edge(a,b,f'M152 {yy[a]+hh[a]/2} V{yy[b]-hh[b]/2}',(169,(yy[a]+yy[b])/2+4),anchor='start')
        for key in ['C','E','H','K']:
            y=yy[key]
            lab='验证窗口\n耗尽' if key=='K' else '未通过'
            d.edge(key,'R',f'M285 {y} H320 V300 H380',(313,y-9 if key!='K' else y-24),lab,anchor='end')
        d.edge('R','RC','M470 317.5 V397.5',(481,361),anchor='start')
        d.edge('RC','FAIL','M470 432.5 V532.5',(481,467),'条件不满足\n或预算耗尽',anchor='start')
        d.edge('R','FAIL','M560 300 H608 V550 H560',(599,500),'不可恢复的\n明确失败',anchor='end')
        d.edge('R','FAULT','M560 300 H637 V685 H560',(628,626),'运动或停止\n状态未知',anchor='end')
        d.edge('RC','A','M380 415 H350 V312 Q362 300 350 288 V7 H12 V45 H29',
               (362,85),'无载荷、运动已知\n且预算允许',anchor='start')
        for key,y in yy.items():d.node(key,152,y,266 if key in 'CEHK' else 246,hh[key])
        for key,y in [('R',300),('RC',415),('FAIL',550),('FAULT',685)]:d.node(key,470,y,180,35)
    elif name=='task-flow':
        d=Drawing(source,650,310)
        poses={'INIT':(80,42),'SELF_CHECK':(240,42),'WAIT_TASK':(400,42),'VALIDATE_TASK':(560,42),
               'SCAN_SCENE':(560,139),'EXECUTE_ITEM':(400,139),'RECORD_RESULT':(240,139),'FINISHED':(80,139)}
        for a,b in [('INIT','SELF_CHECK'),('SELF_CHECK','WAIT_TASK'),('WAIT_TASK','VALIDATE_TASK')]:
            x,y=poses[a];end=poses[b][0];d.edge(a,b,f'M{x+65} {y} H{end-65}')
        d.edge('VALIDATE_TASK','SCAN_SCENE','M560 63 V118')
        d.edge('SCAN_SCENE','EXECUTE_ITEM','M495 139 H465')
        d.edge('EXECUTE_ITEM','RECORD_RESULT','M335 139 H305')
        d.edge('RECORD_RESULT','FINISHED','M175 139 H145',(160,108),'全部完成')
        d.edge('RECORD_RESULT','SCAN_SCENE','M240 160 V192 H560 V160',(400,184),'下一项扫描')
        for key,(x,y) in poses.items():d.node(key,x,y,130,42)
        d.text(15,239,'异常与控制状态（分支未展开）',size=13,anchor='start',bold=True)
        for i,key in enumerate(['RECOVERY','TASK_FAILED','CANCEL_PENDING','CANCELLED','FAULT']):d.node(key,76+i*125,277,116,30)
    elif name=='system-architecture':
        d=Drawing(source,650,490)
        d.edge('UI','TASK','M325 58 V91')
        d.edge('TASK','PICK','M325 139 V181')
        d.edge('CAM','VIS','M50 150 V181')
        d.edge('CAL','VIS','M150 150 V164 H130 V181')
        d.edge('VIS','PICK','M165 205 H215')
        d.edge('TOOL','PICK','M165 295 H192 V222 H215')
        d.edge('PICK','PLAN','M325 229 V271')
        d.edge('PLAN','EXEC','M325 319 V356')
        d.edge('EXEC','ARM','M325 404 V446',(339,430),'实机接入尚未完成',anchor='start')
        d.edge('EXEC','PICK','M435 380 H455 V205 H435')
        d.edge('PICK','TASK','M350 181 V139')
        d.edge('TASK','LOG','M435 115 H550 V271')
        d.edge('VIS','LOG','M90 229 V250 H182 Q192 238 202 250 H313 Q325 238 337 250 H520 V271')
        d.edge('EXEC','LOG','M435 392 H565 V319')
        d.edge('LOG','UI','M635 295 H644 V35 H435')
        d.node('UI',325,35,220,46)
        d.node('TASK',325,115,220,48,'Task：颜色顺序、工位、\n完成数量')
        d.node('PICK',325,205,220,48,'PickPlace：\n单件抓放及结果验证')
        d.node('PLAN',325,295,220,48)
        d.node('EXEC',325,380,220,48,'Motion Execution：\n命令与反馈管理')
        d.node('ARM',325,464,130,36)
        d.node('CAM',50,120,84,60,'固定 RGB-D\n相机')
        d.node('CAL',150,120,96,60,'相机外参、\nCAD 工具变换')
        d.node('VIS',90,205,150,48,'颜色与 SAM 分割、\n几何候选')
        d.node('TOOL',90,295,150,48)
        d.node('LOG',565,295,140,48,'任务状态、错误\n与结果记录')
    else:
        raise ValueError(name)
    return d.save(path)
