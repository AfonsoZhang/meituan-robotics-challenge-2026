import json
from pathlib import Path
import tempfile
import unittest
from summarize_matrix import summarize

class MatrixAccounting(unittest.TestCase):
    def test_failure_and_missing_are_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            trials=[dict(id=str(i),offset_mm=0,mode='correct',repeat=i) for i in range(4)]
            (root/'protocol.json').write_text(json.dumps(dict(trials=trials)))
            for i,(code,summary) in enumerate([(0,dict(passed=True,center_error_mm=2)),
                    (2,dict(passed=False,controller_error_code=0,center_error_mm=300)),
                    (1,dict(passed=False,error='ValueError: Expected exactly one yellow candidate, got 0'))]):
                run=root/str(i);run.mkdir()
                (run/'summary.json').write_text(json.dumps(summary))
                (root/(str(i)+'-process.json')).write_text(json.dumps(dict(exit_code=code,wall_seconds=1)))
            result=summarize(root)
            self.assertFalse(result['complete'])
            self.assertEqual([r['status'] for r in result['trials']],
                ['passed','task_failed','perception_rejected','incomplete'])
            group=next(g for g in result['groups'] if g['mode']=='correct')
            self.assertEqual((group['scheduled'],group['completed'],group['passed']),(4,3,1))
            self.assertEqual(group['errors_mm'],[2,300])

if __name__=='__main__':unittest.main()
