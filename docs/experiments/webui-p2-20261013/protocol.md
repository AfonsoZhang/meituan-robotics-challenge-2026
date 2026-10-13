# Web UI P2 scoped verification — 2026-10-13

USER-HW-20261013-04 / TEAMMATE-WEBUI-P2-20261013 / ENV-WEBUI-P2-20261013. OpenAI Codex assisted implementation, review, testing and evidence preparation.

## Scope and invariants

Eight-module tri-state health, read-only PickPlace/TF observation, optional calibration/trace consumers, complete recorded event query/export. No FSM/Cancel/Motion kernel changes, physical device, production RobotState/ToolState fabrication, baseline promotion or publishing. Preserve Cancel ACK != Stop Confirmed and raw ABORTED/520. Empty/expired/unwired remains unknown. Explicit Goal links only; conflicts quarantine derived ownership.

## Procedure

1. Read fixed PR8/main calibration/Phase2C source. Register new consumer contracts where no producer exists.
2. Run Python offline/HTTP and Node evidence-model tests, including 650-event pagination/export and late/conflicting UUID relationships.
3. Run native ROS fixtures in a new network=none, no-device/no-mount Jazzy container on domain 94 / LOCALHOST. Synthetic RobotState, TF and calibration valid=true are test stimuli, not physical measurements.
4. Build only mtc_cpp_mock_bringup. Repeat the same Python and P2 native checks under the installed namespace, verify installed bytes, and apply the cumulative UI patch to a clean checkout. No full FSM/MoveIt acceptance.
5. Use the configured Windows Playwright browser with an isolated HTTP relay. Native Task → PickPlace → FJT UUIDs, logs and HTTP records come from the actual fixture server. Verify filters, three-view widths and pause/offline behavior. Hidden-tab automation limitations are recorded in qa/browser-validation-notes.md.
6. Preserve complete JSONL/SQLite session files; check SQLite integrity and exact JSONL equality. Stop fixture, relay and container; leave only a no-domain readonly preview.

## Reproduce code checks

```bash
python3 -m unittest discover -s webui -p 'test_*.py'
node --test webui/test_p0.cjs webui/test_p1.cjs webui/test_p2.cjs
# Only in a network-isolated ROS fixture environment, never a robot domain:
python3 -m webui.p2_integration_check --isolated-fixture
python3 -m webui.p1_integration_check --isolated-fixture
python3 -m webui.p0_integration_check --isolated-fixture
```

Actual commands and return codes are in logs/*.command.json. Installed repeats are not extra unique cases. source-sync.json documents namespace conversion; source.patch changes only the Web module and package installation metadata. Full record means all received/recorded session events, not ROS bag or pre-session/unreceived data.

## Results and limitations

See summary.json and development-notes.json. Missing production publishers, hardware/NUC and real calibration remain pending. Browser HTTP export is verified; native Chrome download-to-file was not confirmed. No merge, push, hardware action or formal pin change.
