#!/usr/bin/env bash
set -eo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3-colcon-common-extensions python3-pytest python3-yaml ros-jazzy-ament-cmake-gtest ros-jazzy-ament-lint-auto ros-jazzy-ament-lint-common
