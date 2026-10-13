set -e
docker run -d --name mtc-main-review-b418515 --network none --cpus 2 --memory 4g --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges --label mtc.purpose=main-acceptance --label mtc.commit=b4185155383541e1a4161587c4049a162f74b36d mtc-trajectory-ownership-review:681bb64 sleep infinity
docker inspect mtc-main-review-b418515 > outputs/main-acceptance-20261013-b418515/meta/isolation.json
docker exec mtc-main-review-b418515 mkdir -p /candidate /review /review-tools
docker cp outputs/main-acceptance-20261013-b418515/source/. mtc-main-review-b418515:/candidate/
docker cp robot/probe_task_mock.py mtc-main-review-b418515:/review-tools/
docker cp robot/probe_moveit.py mtc-main-review-b418515:/review-tools/
docker cp robot/probe_cpp_actions.py mtc-main-review-b418515:/review-tools/
