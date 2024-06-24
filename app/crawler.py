import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import boto3
from pydantic import BaseModel
import jpholiday

from lib.common.secrets import get_secret_value_factory, SecretValue
from lib.common.model import TimeCardSetting
from lib.env import get_env, Environment


# メッセージをパースして表示
class SqsMessageBody(BaseModel):
    username: str

def sqs_send_message(sqs_url: str, aws_region: str, message: SqsMessageBody):
    # SQSクライアントの生成
    sqs_client = boto3.client('sqs', region_name=aws_region)
    response = sqs_client.send_message(
        QueueUrl=env.sqs_url,
        MessageBody=message.model_dump_json()
    )
    return response

def scan_dynamo_table(dynamo_client, table_name) -> List[Dict[str, Any]]:
    response = dynamo_client.scan(TableName=table_name)
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = dynamo_client.scan(
            TableName=table_name,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))
    return items


def main(env: Environment, secret_value: SecretValue, dynamodb_client, now: datetime):
    begine = now.replace(
        minute=(now.minute // 5) * 5,  # 5分単位に丸める
        second=0,
        microsecond=0
    )
    end = begine + timedelta(minutes=5)
    is_holiday = jpholiday.is_holiday(now)
    print(f"begine: {begine}, end: {end}, weekday: {now.weekday()}, is_holiday: {is_holiday}")
    weekday = now.weekday()
    if is_holiday or weekday >= 5:  # 土日祝日なら終了
        print("Today is holiday or weekend")
        exit()
    for item in scan_dynamo_table(dynamodb_client, env.dynamo_table_name):
        try:
            username = item["username"]["S"]
            setting = TimeCardSetting.model_validate_json(item["setting"]["S"])
            if not setting.enabled:
                continue

            if weekday == 0:
                clock_in = setting.setting.Mon.clock_in
                clock_out = setting.setting.Mon.clock_out
            elif weekday == 1:
                clock_in = setting.setting.Tue.clock_in
                clock_out = setting.setting.Tue.clock_out
            elif weekday == 2:
                clock_in = setting.setting.Wed.clock_in
                clock_out = setting.setting.Wed.clock_out
            elif weekday == 3:
                clock_in = setting.setting.Thu.clock_in
                clock_out = setting.setting.Thu.clock_out
            elif weekday == 4:
                clock_in = setting.setting.Fri.clock_in
                clock_out = setting.setting.Fri.clock_out
            else:
                continue
            clock_in_time = datetime.strptime(clock_in, "%H:%M")
            clock_in_datetime = begine.replace(hour=clock_in_time.hour, minute=clock_in_time.minute, second=0, microsecond=0)
            print(f"clock_in_datetime: {clock_in_datetime}")

            clock_out_time = datetime.strptime(clock_out, "%H:%M")
            clock_out_datetime = begine.replace(hour=clock_out_time.hour, minute=clock_out_time.minute, second=0, microsecond=0)
            print(f"clock_out_datetime: {clock_out_datetime}")

            message = SqsMessageBody(username=username)
            if (clock_in_datetime >= begine and clock_in_datetime < end):
                print(f"{username}: 出勤")
                sqs_send_message(env.sqs_url, env.aws_region, message)
            elif (clock_out_datetime >= begine and clock_out_datetime < end):
                print(f"{username}: 退勤")
                sqs_send_message(env.sqs_url, env.aws_region, message)
            else:
                print(f"{username}: スキップ")
        except Exception as e:
            print("{}\n{}".format(str(e), traceback.format_exc()))
            # TODO: 通知

if __name__ == "__main__":
    now = datetime.now()
    env = get_env()

    secret_value = get_secret_value_factory(env.secret_name, env.aws_region)()

    dynamodb_client = boto3.client('dynamodb', region_name=env.aws_region)

    main(env, secret_value, dynamodb_client, now)
