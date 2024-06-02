from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from pydantic_settings import BaseSettings

class Environment(BaseSettings):
    client_code: str
    username: str
    password: str

env = Environment()

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

username.send_keys(env.username)
client_code.send_keys(env.client_code)
password.send_keys(env.password)

login_button = driver.find_element(By.ID, "login_button")  # ログインボタンのname属性を指定
login_button.click()
driver.implicitly_wait(3)

driver.save_screenshot("./tmp/login.png")

driver.get("https://ssl.jobcan.jp/jbcoauth/login")

driver.save_screenshot("./tmp/kintai.png")

# 退勤ボタンをクリック
#adit_btn = driver.find_element(By.ID, "adit-button-push")
#adit_btn.click()
# driver.implicitly_wait(3)

driver.save_screenshot("./tmp/adit.png")

title = driver.title
print(title)