import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pydantic_settings import BaseSettings
from pydantic import BaseModel

# 環境変数
class Environment(BaseSettings):
    app_bucket: str
    sqs_url: str
    aws_region: str = "ap-northeast-1"
env = Environment()

sqs_client = boto3.client('sqs', region_name=env.aws_region)

# キューからメッセージを取り出す
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html
response = sqs_client.receive_message(
    QueueUrl=env.sqs_url,
    MaxNumberOfMessages=1,  # 取得するメッセージの最大数
    WaitTimeSeconds=10, # ポーリングの待ち時間
)
messages = response.get("Messages", [])

# メッセージが存在しない場合はそのまま終了
if len(messages) <= 0:
    exit()

# 取得したメッセージを削除
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/delete_message.html
sqs_client.delete_message(
    QueueUrl=env.sqs_url,
    ReceiptHandle=messages[0]["ReceiptHandle"],
)

# メッセージをパースして表示
class QueueMessageBody(BaseModel):
    client_code: str
    username: str
    password: str
body = QueueMessageBody.model_validate_json(messages[0]["Body"])
print(body)

# 打刻処理
chrome_options = Options()
chrome_options.add_argument("--headless")  # ヘッドレスモードを有効にする
chrome_options.add_argument("--disable-gpu")  # 可能であればGPUの使用を無効にする
chrome_options.add_argument("--no-sandbox")    # サンドボックスモードを無効にする（特定の環境で必要）

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://ssl.jobcan.jp/jbcoauth/login")

driver.implicitly_wait(1)

client_code_btn = driver.find_element(By.ID, "client_code_link")
client_code_btn.click()

driver.implicitly_wait(1)

username = driver.find_element(By.ID, "user_email")  # ユーザー名入力欄のname属性を指定
client_code = driver.find_element(By.ID, "user_client_code")  # ユーザー名入力欄のname属性を指定
password = driver.find_element(By.ID, "user_password")  # パスワード入力欄のname属性を指定

username.send_keys(body.username)
client_code.send_keys(body.client_code)
password.send_keys(body.password)

login_button = driver.find_element(By.ID, "login_button")  # ログインボタンのname属性を指定
login_button.click()
driver.implicitly_wait(3)

driver.save_screenshot("tmp/login.png")

driver.get("https://ssl.jobcan.jp/jbcoauth/login")

driver.save_screenshot("tmp/kintai.png")

# 退勤ボタンをクリック
#adit_btn = driver.find_element(By.ID, "adit-button-push")
#adit_btn.click()
# driver.implicitly_wait(3)

driver.save_screenshot("tmp/adit.png")

s3_client = boto3.client('s3', region_name=env.aws_region)

screenshots = ["tmp/login.png", "tmp/kintai.png", "tmp/adit.png"]
for screenshot in screenshots:
    s3_key = f"kintaro/{screenshot}"
    with open(screenshot, "rb") as f:
        s3_client.put_object(Bucket=env.app_bucket, Key=s3_key, Body=f)

title = driver.title
print(title)