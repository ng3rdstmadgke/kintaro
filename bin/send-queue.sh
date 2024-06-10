#!/bin/bash
set -eu

cd $CONTAINER_PROJECT_ROOT
export SQS_URL=$(cd ${CONTAINER_PROJECT_ROOT}/terraform/env/prd && terraform output -raw app_sqs_url)
cd $CONTAINER_PROJECT_ROOT/app
poetry run python send_message.py
