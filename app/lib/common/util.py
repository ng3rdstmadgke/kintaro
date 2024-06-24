from lib.common.model import TimeCardSetting

def get_setting_or_default(dynamodb_client, dynamo_table_name: str, username: str) -> TimeCardSetting:
    item = dynamodb_client.get_item(
        TableName=dynamo_table_name,
        Key={"username": {"S": username}}
    )
    try:
        timecard_setting = item["Item"]["setting"]["S"]
        return TimeCardSetting.model_validate_json(timecard_setting)
    except KeyError:
        return TimeCardSetting.model_validate({
          "enabled": False,
          "jobcan_id": "",
          "jobcan_password": "",
          "setting": {
              "Mon": {"clock_in": "09:00", "clock_out": "18:00"},
              "Tue": {"clock_in": "09:00", "clock_out": "18:00"},
              "Wed": {"clock_in": "09:00", "clock_out": "18:00"},
              "Thu": {"clock_in": "09:00", "clock_out": "18:00"},
              "Fri": {"clock_in": "09:00", "clock_out": "18:00"},
          }
        })
