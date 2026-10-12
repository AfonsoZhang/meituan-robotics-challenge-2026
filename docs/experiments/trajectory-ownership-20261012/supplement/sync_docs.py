"""Add current acceptance facts while preserving historical signed reports. Codex assisted."""
from pathlib import Path
import json
raw=Path(__file__).resolve().parent;root=raw.parents[1];f=json.loads((raw/'freeze-result.json').read_text());count=f['files']
obs='ENV-TRAJECTORY-OWNERSHIP-20261012';ref='TEAMMATE-OWNERSHIP-20261012'
files=['README.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/upstream-monitor.md','robot/README.md']
for n in files:assert obs not in (root/n).read_text(),n
def row(s,prefix,note):
 lines=s.splitlines();indices=[i for i,l in enumerate(lines) if l.startswith(prefix)];assert len(indices)==1,prefix
 k=indices[0];assert lines[k].endswith(' |');lines[k]=lines[k][:-2]+'；'+note+' |';return '\n'.join(lines)+'\n'
p=root/'README.md';s=p.read_text();anchor='**个人分工：系统集成与验收，兼做 Web UI**';assert s.count(anchor)==1
s=s.replace(anchor,f'''**轨迹Goal归属补验（10月12日）：** `681bb64…` 首次FJT套件在重复取消用例120秒超时、XML缺失；同一未改二进制61项补跑及独立478项UBSan通过，间歇超时仍回交孙嘉明。新的原生GenericSystem预检缺少实时Status，默认MoveIt共存还有2个FJT客户端，两者均BLOCKED、零Goal；不能沿用45f497c四场景PASS。见[归属与Status验收](docs/trajectory-ownership-acceptance.md)（{ref}；{obs}），{count}文件冻结。原始失败保留，正式基线不变，08:00集成/UI任务未提前启动。

'''+anchor)
anchor='- [个人主责：系统集成与验收]';assert s.count(anchor)==1
s=s.replace(anchor,'- [轨迹Goal归属与实时Status验收](docs/trajectory-ownership-acceptance.md)：首次120秒超时、61项补跑/478项UBSan与原生门禁阻断分开记录。\n'+anchor);p.write_text(s)
p=root/'docs/hardware-vision-plan.md';s=p.read_text()
s=row(s,'| I01 |',f'681bb64首次FJT61项套件120秒超时（417项其他C++ XML通过），同二进制61项补跑及独立478项UBSan通过；未关闭间歇挂起（{obs}）')
s=row(s,'| I03 |',f'681bb64新增实时Status证据门禁，原生GenericSystem received/fresh/ready=0，success零Goal BLOCKED；默认MoveIt共存clients=2也BLOCKED，旧45f497c四项执行通过仅为历史（{obs}）')
s=row(s,'| I04 |',f'pending UUID精确归属测试补验完成，原生Status/独占证据契约及异步Cancel宿主仍缺；完整Task→PickPlace与Web UI集成保留08:00后范围（{obs}）')
s+=f'''
## 2026-10-12 Goal归属与实时Status补验

{ref} / {obs}：681bb64相对45f497c的7文件改变轨迹端口pending UUID归属、Status合法性/接收龄和终态顺序门禁，新增15项受控真实DDS测试；Snapshot布局变化要求消费者重建。原始15包构建、269 Python/15 E2E/6 ROS通过，但FJT第7项DuplicateCancelOnlyOneBackendCall120秒超时，原XML为missing_result。其他417项C++ XML通过；同一未改二进制61项一次补跑及独立478项UBSan通过。原挂起没有现场线程栈，尚不能判定夹具/端口/中间件原因，交孙嘉明保留最小触发和差异分析。

原生GenericSystem预检未收到Status，零Goal拒绝；测试夹具专用心跳不能当原生契约。默认move_group共存形成2个FJT客户端，再次零Goal BLOCKED。没有预热动作/伪造Status/放宽参数，原生其余执行场景NOT RUN，不沿用上轮四项PASS。完整FSM、异步Cancel/停稳宿主、Planner/FJT时间及独占执行契约仍未完成。固定MoveIt退出-11和旧Python220/510/520继续保留。{count}文件及清理见[验收报告](trajectory-ownership-acceptance.md)。08:00统一C++Mock/UI仍待触发，未修改内核、合并或推进正式基线；OpenAI Codex协助复现和登记。
''';p.write_text(s)
p=root/'docs/open-questions.md';s=p.read_text()
s=row(s,'| Q17',f'681bb64独立UBSan478通过不关闭原FJT重复取消120秒挂起；原生Status门禁拒绝零Goal，固定MoveIt退出-11保留（{obs}）')
s=row(s,'| Q18',f'681bb64的61项补跑通过但首次套件超时仍待孙嘉明归因；原生GenericSystem实时Status及默认MoveIt双客户端阻断，完整链路未过（{ref}；{obs}）')
s+=f'''
## 2026-10-12 Goal归属更新后的实验缺口

{ref} / {obs}：首次FJT套件120秒停在DuplicateCancelOnlyOneBackendCall，missing_result保留；61项同二进制补跑和478项UBSan通过只说明各次运行结果，不证明挂起已修复。没有原现场线程栈，孙嘉明需区分夹具与生产端口锁/生命周期或ROS调度原因，保留有界失败复现与回归。

新的Status门禁在原生GenericSystem无实时Status时拒绝首个Goal；有效接收年龄不等于绝对新鲜度或跨进程互斥。默认MoveIt额外FJT客户端仍阻断。应由孙嘉明确认可信Status/单一执行管理契约，常建烁和集成共同确认规划时基和执行权；不得通过空数组、心跳、预热Goal或修改限制换取通过。原生cancel/mismatch/identity未执行，独立Fake61测试不替代原生/完整FSM。旧Python220/510/520、MoveIt退出-11、依赖/驱动lint、SDK/TSan/NUC/实机缺口不变。见[报告](trajectory-ownership-acceptance.md)与{count}文件冻结，08:00后C++Mock/UI任务未提前运行。
''';p.write_text(s)
p=root/'docs/upstream-monitor.md';s=p.read_text();s+=f'''
## Goal归属与实时Status事件

`681bb64…`（{ref}）的25步固定复现完整、317原文件哈希一致，一次投递约{f['queue_to_ack_seconds']:.3f}秒ACK。新增的真实失败为FJT套件第7项DuplicateCancelOnlyOneBackendCall120秒超时；本轮新核验器也对原XML报missing_result。确认runner59420/旧容器停止后补跑同二进制61项及独立UBSan478项均通过，原挂起不关闭（{obs}）。

原生GenericSystem无实时Status，success预检零Goal BLOCKED；加默认MoveIt再因Status及clients=2阻断。无心跳/预热Goal/参数放宽，未补跑原生其余执行场景。原失败、新结果和清理{count}文件见[验收报告](trajectory-ownership-acceptance.md)。空域、进程及容器停止后归档并complete，只释放下一SHA串行门禁，不等于功能全通过。08:00后集成/UI定时器继续SCHEDULED；原监测60秒轮询、固定主会话和08:00截止不变，没有queue或新监测。
''';p.write_text(s)
p=root/'robot/README.md';s=p.read_text();anchor='## SDK 与 Jazzy 驱动资料已核对';assert s.count(anchor)==1
s=s.replace(anchor,f'''681bb64轨迹Goal归属/Status补验（{ref}；{obs}）：原FJT套件重复取消120秒超时；同二进制61项补跑、独立478项UBSan通过，但间歇挂起仍交孙嘉明。原生GenericSystem无Status及默认MoveIt双客户端均BLOCKED零Goal，旧45f497c四项执行PASS不沿用。{count}文件、原失败和清理见[归属验收](../docs/trajectory-ownership-acceptance.md)，未修改内核/正式基线；完整C++Mock/UI后续任务仍等08:00。

'''+anchor);p.write_text(s)
print('UPDATED',*files)
