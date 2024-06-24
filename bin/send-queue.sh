#!/bin/bash
set -eu

USERNAME=$1

if [ -z "$USERNAME" ]; then
  echo "Usage: $0 <USERNAME>"
  exit 1
fi

cd $CONTAINER_PROJECT_ROOT
export SQS_URL=$(cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd && terraform output -raw app_sqs_url)
cd $CONTAINER_PROJECT_ROOT/app
poetry run python send_message.py "$USERNAME"
