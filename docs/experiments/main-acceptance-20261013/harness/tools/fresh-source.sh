set -e
docker exec mtc-main-review-b418515 test ! -e /main-source
docker exec mtc-main-review-b418515 mkdir /main-source
docker cp outputs/main-acceptance-20261013-b418515/source/. mtc-main-review-b418515:/main-source/
docker exec mtc-main-review-b418515 git -C /main-source status --porcelain
