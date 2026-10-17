#!/usr/bin/env bash
# Uses the fixed teammate workspace path as a reference, configurable on the NUC.
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo '未找到 ROS 2 Jazzy。仅预览离线页面可运行 python3 -m webui.server。' >&2
  exit 1
fi
source /opt/ros/jazzy/setup.bash
MTC_UI_SETUP="${MTC_UI_SETUP:-/home/aaet/meituan_challenge_ws/install/setup.bash}"
if [[ ! -f "$MTC_UI_SETUP" ]]; then
  echo "未找到接口工作空间：$MTC_UI_SETUP；请设置 MTC_UI_SETUP 为实际 install/setup.bash。" >&2
  exit 1
fi
source "$MTC_UI_SETUP"
exec /usr/bin/python3 -m webui.server "$@"
