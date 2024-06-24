# 事前準備

環境変数ファイルの準備

```bash
vim .env
```

```.env
DYNAMO_TABLE_NAME=kintaro-prd-users
SECRET_NAME=/kintaro/prd/app
APP_BUCKET=kintaro-app
SQS_URL=https://sqs.ap-northeast-1.amazonaws.com/xxxxxxxxxxxx/kintaro-prd-TimecardJobQueue
```


# アプリの動作確認

```bash
./bin/run.sh app
```

# Jobの動作確認

```bash
# 打刻はしません、スクリーンショットをs3にアップロードします
./bin/run.sh job <DynamoDBに登録されているユーザー名>
```

# Crawlerの動作確認

```bash
# dynamodbを読み取って実際にSQSにキューイングします
./bin/run.sh crawler
```