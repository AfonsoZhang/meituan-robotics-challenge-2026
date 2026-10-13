set +e
mkdir -p /c1-evidence/red-tests
timeout 25 /c1-build/mtc_ros2_action_cpp/test_action_contracts --gtest_filter=ActionContracts.DelayedCancelSamplesKnownStationaryMockBeforeValidatingStop --gtest_output=xml:/c1-evidence/red-tests/contracts.xml
contracts=$?
timeout 30 /c1-build/mtc_ros2_action_cpp/test_pick_place_action --gtest_filter=PickAction.DelayedCancel* --gtest_output=xml:/c1-evidence/red-tests/pick.xml
pick=$?
python3 - "$contracts" "$pick" <<'INNER'
import json,sys
from pathlib import Path
r=dict(contracts_exit=int(sys.argv[1]),pick_exit=int(sys.argv[2]),expected_failure_exit=1)
Path('/c1-evidence/red-tests/exit-codes.json').write_text(json.dumps(r,indent=2)+'\n')
assert r['contracts_exit']==1 and r['pick_exit']==1, r
INNER
