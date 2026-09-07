"""Audit every scheduled trial and summarize without discarding failures."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def summarize(root):
    protocol=json.loads((root/'protocol.json').read_text())
    rows=[]
    for trial in protocol['trials']:
        run=root/trial['id']; audit=root/(trial['id']+'-process.json')
        if not audit.exists():
            rows.append(dict(**trial,status='incomplete',passed=False));continue
        process=json.loads(audit.read_text())
        summary=json.loads((run/'summary.json').read_text()) if (run/'summary.json').exists() else {}
        passed=bool(process['exit_code']==0 and summary.get('passed',False))
        if passed:status='passed'
        elif summary.get('controller_error_code') is not None:status='task_failed'
        elif any(s in summary.get('error','') for s in ('yellow candidate','quality gate','Correction exceeds','detection geometry')):status='perception_rejected'
        else:status='runtime_or_pregrasp_failure'
        vision=summary.get('vision',{})
        delta=vision.get('delta_xy_m')
        rows.append(dict(**trial,status=status,passed=passed,exit_code=process['exit_code'],
            center_error_mm=summary.get('center_error_mm'),
            observed_lift_duration_s=summary.get('observed_lift_duration_s'),
            bystanders=summary.get('bystanders'),observer_displacement_m=vision.get('observer_max_battery_displacement_m'),
            measured_delta_xy_mm=[v*1000 for v in delta] if delta else None,
            error=summary.get('error'),wall_seconds=process['wall_seconds'],
            summary_sha256=hashlib.sha256((run/'summary.json').read_bytes()).hexdigest() if (run/'summary.json').exists() else None))
    groups=[]
    for offset in sorted(set(r['offset_mm'] for r in rows)):
        for mode in ('observe','correct'):
            subset=[r for r in rows if r['offset_mm']==offset and r['mode']==mode]
            errors=[r['center_error_mm'] for r in subset if r.get('center_error_mm') is not None]
            groups.append(dict(offset_mm=offset,mode=mode,scheduled=len(subset),
                completed=sum(r['status']!='incomplete' for r in subset),passed=sum(r['passed'] for r in subset),
                errors_mm=errors,median_error_mm=statistics.median(errors) if errors else None))
    return dict(protocol_sha256=hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest(),
        complete=all(r['status']!='incomplete' for r in rows),trials=rows,groups=groups,
        limitations='Two repeats per condition; same ideal simulator and no injected noise. Descriptive counts, not estimated hardware reliability. Missing trials remain incomplete.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args();result=summarize(args.root)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    print(text)
