#!/bin/bash
set -e

SCRIPT_DIR=$(cd $(dirname $0); pwd)

cat <<EOF >> ~/.bashrc

source ${SCRIPT_DIR}/.bashrc_private
EOF

(
  cd $CONTAINER_PROJECT_ROOT/app;
  poetry install
)