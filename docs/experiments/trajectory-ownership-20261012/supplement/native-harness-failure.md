# Native preflight observer failure retained

The original delivered success probe printed Status received=0/fresh=0/ready=0 and BLOCKED, exited1 as its source specifies (catch returns code1). The observer incorrectly expected2, which is the topology/invalid-argument code, and asserted before launching MoveIt. No source or original evidence changed. First native-gate/summary remains FAIL. Only the control launch existed: exit0, no escalation or child failure, daemon stopped and domain empty; summary clean_shutdown FAIL also reflects the wrapper requiring2 launches. Statistics context errors retained. No Goal sent on the delivered preflight return path.

After process cleanup, a separate domain156 topology-only run covers the previously unexecuted coexistence branch. The native success probe is not repeated. Both scripts and all failed logs are frozen. OpenAI Codex assisted; acceptance-harness mistake, not attributed to the upstream kernel.
