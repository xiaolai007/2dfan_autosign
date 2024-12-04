from DrissionPage import Chromium
from bypass_captcha import CaptchaBypasser,ImageMatcher
import time
import os
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # 启动或接管浏览器，并创建标签页对象
    logging.info("启动浏览器...")
    tab = Chromium().latest_tab
    logging.info("浏览器已启动并获取标签页对象")

    # 跳转到登录页面
    logging.info("跳转到登录页面...")
    tab.get("https://2dfan.com/users/421136/recheckin")
    logging.info("已跳转到登录页面")

    # 定位到账号文本框并输入账号
    user_email = os.getenv('USER_EMAIL')
    if not user_email:
        raise ValueError("环境变量 USER_EMAIL 未设置")
    logging.info(f"输入账号：{user_email}")
    tab.ele('@name=login').input(user_email)

    # 定位到密码文本框并输入密码
    user_password = os.getenv('USER_PASSWORD')
    if not user_password:
        raise ValueError("环境变量 USER_PASSWORD 未设置")
    logging.info("输入密码")
    tab.ele('@name=password').input(user_password)

    # 等待页面加载
    logging.info("等待页面加载...")
    time.sleep(12)

    # 查找并点击“确认您是真人”复选框
    logging.info("初始化验证码绕过程序...")
    captcha_bypasser = CaptchaBypasser()
    logging.info("运行验证码绕过程序...")
    captcha_bypasser.run()
    time.sleep(12)

    # 定位到登录按钮并点击
    logging.info("查找并点击登录按钮...")
    login_button = tab.ele('@type=submit')
    if login_button:
        login_button.click()
        logging.info("登录按钮已点击")
    else:
        raise RuntimeError("未找到登录按钮")
    # time.sleep(16)
    # 循环检测直到匹配成功
    logging.info("开始匹配截图与模板...")
    match_found = False
    timeout = 60  # 设置超时时间（秒）
    start_time = time.time()

    while not match_found:
        if time.time() - start_time > timeout:
            raise TimeoutError("匹配超时，未能检测到模板！")

        # 截图保存到当前目录
        screenshot_path = "current_screenshot.png"
        tab.get_screenshot(name=screenshot_path, full_page=True)

        # 实例化 ImageMatcher
        image_matcher = ImageMatcher(
            source_image_path=screenshot_path,
            template_image_path="captcha-verify-you-are-human-eg.png",
        )

        # 计算匹配准确度
        accuracy = image_matcher.accuracy()
        logging.info(f"当前匹配准确度: {accuracy}")

        if accuracy > 0.25:
            logging.info("匹配成功，检测页面签到状态...")
            match_found = True
        else:
            logging.info("匹配失败，等待1秒后重新检测...")
            time.sleep(1)

    tab.get_screenshot(name='pic1.png', full_page=True)

    # 检测页面中是否包含“今日已签到”文本
    checkin_status = tab.ele('text:今日已签到')
    if checkin_status:
        logging.info("已签到！")
    else:
        logging.info("未签到！")
        # 再次检查验证码绕过
        logging.info("再次运行验证码绕过程序...")
        captcha_bypasser = CaptchaBypasser()
        captcha_bypasser.run()
        time.sleep(12)

        # 定位到签到按钮并点击
        logging.info("查找并点击签到按钮...")
        checkin_button = tab.ele('@type=submit')
        if checkin_button:
            checkin_button.click()
            logging.info("签到按钮已点击")
        else:
            raise RuntimeError("未找到签到按钮")
        time.sleep(5)

        tab.refresh()  # 刷新页面

        # 检测页面中是否包含“今日已签到”文本
        checkin_status = tab.ele('text:今日已签到')
        if checkin_status:
            logging.info("签到成功！")
        else:
            logging.info("签到失败！")

except Exception as e:
    logging.error(f"运行过程中发生错误: {e}")
finally:
    # 确保浏览器在脚本结束时关闭
    logging.info("关闭浏览器...")
    tab.close()
    logging.info("浏览器已关闭")

