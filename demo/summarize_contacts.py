"""Summarize sampled blue contact pairs; endpoints are not contact durations."""
import argparse
import json
from pathlib import Path

def summarize(samples):
    pairs={}
    for s in samples:
        if s['elapsed_s'] is None:continue
        for pair in s['pairs']:
            key=' | '.join(pair)
            p=pairs.setdefault(key,dict(sample_count=0,first_elapsed_s=s['elapsed_s'],last_elapsed_s=s['elapsed_s']))
            p['sample_count']+=1;p['last_elapsed_s']=s['elapsed_s']
    return {'scope':'Blue battery only; sampled contact names, not a full collision audit. First/last samples do not imply continuous contact.', 'pairs':pairs}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('contacts',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args();result=summarize(json.loads(args.contacts.read_text()))
    text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    print(text)
