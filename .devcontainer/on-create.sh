#!/bin/bash
SCRIPT_DIR=$(cd $(dirname $0); pwd)

cat <<EOF >> ~/.bashrc

source ${SCRIPT_DIR}/.bashrc_private
EOF