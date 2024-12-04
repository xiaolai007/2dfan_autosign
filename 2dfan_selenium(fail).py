import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
from bypass_captcha import CaptchaBypasser

from selenium.webdriver.common.action_chains import ActionChains

# 设置浏览器选项
options = uc.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
options.add_argument('--disable-blink-features=AutomationControlled')  # 隐藏自动化特征

# 启动 undetected-chromedriver
driver = uc.Chrome(options=options)

# 打开目标页面
driver.get("https://2dfan.com/users/421136/recheckin")
time.sleep(3)  # 等待页面加载
try:
    # 查找并填写用户名
    username_field = driver.find_element(By.NAME, "login")
    username_field.send_keys("xxx")
    time.sleep(1)

    # 查找并填写密码
    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys("xxx")
    time.sleep(2)

    # 查找并点击“确认您是真人”复选框
    captcha_bypasser = CaptchaBypasser()
    captcha_bypasser.run()
    time.sleep(5)

    # 查找并点击登录按钮
    login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), '登录')]")
    ActionChains(driver).move_to_element(login_button).click().perform()
    time.sleep(3)  # 等待登录操作完成

    print("登录操作成功完成！")

except Exception as e:
    print("登录过程中出错：", e)

finally:
    # 关闭浏览器
    driver.quit()