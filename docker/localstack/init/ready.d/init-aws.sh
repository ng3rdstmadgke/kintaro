#!/bin/bash

# LocalStack - init-fooks: https://docs.localstack.cloud/references/init-hooks/
# デバッグコマンド: docker logs terraform-tutorial_devcontainer-localstack-1  | less
# set -ex
set -e

#printenv

APP_NAME=kintaro
STAGE_NAME=local
REGION=ap-northeast-1

#
# DynamoDB
#
awslocal dynamodb create-table \
  --region ${REGION} \
  --table-name ${APP_NAME}-${STAGE_NAME}-Users \
  --attribute-definitions AttributeName=username,AttributeType=S \
  --key-schema AttributeName=username,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

SETTING=$(
cat <<EOF | tr -d '\n'
{
  \"enabled\": true,
  \"jobcan_id\": \"123456789\",
  \"jobcan_password\": \"password\",
  \"setting\": {
    \"Mon\": {\"clock_in\": \"09:00\", \"clock_out\": \"18:00\"},
    \"Tue\": {\"clock_in\": \"09:00\", \"clock_out\": \"18:00\"},
    \"Wed\": {\"clock_in\": \"09:00\", \"clock_out\": \"18:00\"},
    \"Thu\": {\"clock_in\": \"09:00\", \"clock_out\": \"18:00\"},
    \"Fri\": {\"clock_in\": \"09:00\", \"clock_out\": \"18:00\"}
  }
}
EOF
)

for username in "user1" "user2" "user3"; do
  awslocal dynamodb put-item \
    --region ${REGION} \
    --table-name ${APP_NAME}-${STAGE_NAME}-Users \
    --item "{
      \"username\": {\"S\": \"$username\"},
      \"setting\": {\"S\": \"$SETTING\" }
    }"
done

#
# SQL
#
awslocal sqs create-queue \
  --region ${REGION} \
  --queue-name ${APP_NAME}-${STAGE_NAME}-TimecardJobQueue