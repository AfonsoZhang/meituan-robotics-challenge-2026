set -e
python3 - <<'INNER'
import subprocess,json
for row in json.loads(subprocess.check_output(['docker','inspect','mtc-main-review-b418515','mtc-cpp-webui-review'])):
 assert not row['State']['Running'], row['Name']
INNER
docker run -d --name mtc-pr8-c1-review-20261013 --network none --cpus 2 --memory 4g --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges --label mtc.purpose=pr8-c1-acceptance --label mtc.commit=7da43228d602a6b23571bfc599d69529ef7bea23 mtc-trajectory-ownership-review:681bb64 sleep infinity
docker exec mtc-pr8-c1-review-20261013 mkdir /pr8-source /pr8-review /pr8-tools
docker cp outputs/main-acceptance-20261013-b418515/pr8-source/. mtc-pr8-c1-review-20261013:/pr8-source/
docker cp outputs/main-acceptance-20261013-b418515/tools/. mtc-pr8-c1-review-20261013:/pr8-tools/
docker inspect mtc-pr8-c1-review-20261013 > outputs/main-acceptance-20261013-b418515/meta/pr8-isolation.json
