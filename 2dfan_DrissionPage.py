import time, os
import logging
from DrissionPage import ChromiumPage
from bypass_captcha import CaptchaBypasser
from DrissionPage import ChromiumOptions

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量
LOGIN_URL = "https://2dfan.com/users/421136/recheckin"
MAX_RETRIES = 3     # 最大重试次数

def locate_button(ele, tag="tag:svg", retries=MAX_RETRIES):
    """
    尝试定位按钮，最多尝试 `retries` 次。
    """
    for attempt in range(retries):
        try:
            button = ele.parent().shadow_root.child()(f"tag:body").shadow_root(tag)
            if button:
                logging.info(f"按钮定位成功 (尝试次数: {attempt + 1})")
                return button
            else:
                logging.warning(f"按钮为空，重新尝试定位 (尝试次数: {attempt + 1})")
        except Exception as e:
            logging.error(f"定位按钮时出错: {e} (尝试次数: {attempt + 1})")
        time.sleep(1)
    raise RuntimeError("按钮定位失败，已达到最大重试次数")

def process_captcha(tab, eles, tag="tag:circle"):
    """
    定位验证码中相关元素并返回该元素。
    """
    for ele in eles:
        if "name" in ele.attrs and "type" in ele.attrs:
            if "turnstile" in ele.attrs["name"] and ele.attrs["type"] == "hidden":
                button = locate_button(ele, tag=tag)
                logging.info(f"验证相关按钮：{button}")
                tab.wait(1)
                return button
    raise RuntimeError("未找到验证码相关按钮")

def main():
    try:
        # 启动浏览器
        logging.info("启动浏览器...")
        co = ChromiumOptions()
        # 禁止所有弹出窗口
        # co.set_pref(arg='profile.default_content_settings.popups', value='0')
        # # 隐藏是否保存密码的提示
        # co.set_pref('credentials_enable_service', False)

        #设置无痕模式
        co.incognito(True)
        tab = ChromiumPage(co)

        # 跳转到登录页面
        logging.info("跳转到登录页面...")
        tab.get(LOGIN_URL)
        logging.info("已跳转到登录页面")

        # 输入账号
        user_email = os.getenv("USER_EMAIL", "")
        if not user_email:
            raise ValueError("环境变量 USER_EMAIL 未设置")
        logging.info(f"输入账号: {user_email}")
        tab.ele('@name=login').input(user_email)

        # 输入密码
        user_password = os.getenv("USER_PASSWORD", "")
        if not user_password:
            raise ValueError("环境变量 USER_PASSWORD 未设置")
        logging.info("输入密码")
        tab.ele('@name=password').input(user_password)
        
        tab.wait.eles_loaded("tag:input")
        eles = tab.eles("tag:input")

        # 验证验证码
        button = process_captcha(tab, eles, tag="tag:svg")
        tab.wait.ele_hidden(button)
        logging.info("开始验证")
        tab.wait(3)

        # 初始化验证码绕过程序
        logging.info("初始化验证码绕过程序...")
        captcha_bypasser = CaptchaBypasser()
        logging.info("运行验证码绕过程序...")
        captcha_bypasser.run()

        # 检验是否成功
        button = process_captcha(tab, eles, tag="tag:circle")
        tab.wait.ele_displayed(button)
        logging.info("验证成功")
        tab.wait(3)
        tab.get_screenshot(name='pic1.png', full_page=True)

        # 点击登录按钮
        logging.info("查找并点击登录按钮...")
        login_button = tab.ele('@type=submit')
        if login_button:
            login_button.click()
            logging.info("登录按钮已点击")
        else:
            raise RuntimeError("未找到登录按钮")

        # 等待页面加载
        tab.wait.new_tab()
        tab.wait.eles_loaded("tag:input")
        eles = tab.eles("tag:input")
        logging.info("登录成功")
        tab.get_screenshot(name='pic2.png', full_page=True)

        tab.get_screenshot(name='pic3.png', full_page=True)

        # 检测签到状态
        checkin_status = tab.ele('text:今日已签到')
        if checkin_status:
            logging.info("今日已签到！")
        else:
            logging.info("未签到，尝试签到...")

            # 再次运行验证码绕过程序
            logging.info("再次运行验证码绕过程序...")
            captcha_bypasser.run()

            # 检验是否成功
            button = process_captcha(tab, eles, tag="tag:circle")
            tab.wait.ele_displayed(button)
            logging.info("验证成功")
            tab.get_screenshot(name='pic4.png', full_page=True)
            tab.wait(1)

            # 点击签到按钮
            logging.info("查找并点击签到按钮...")
            tab.get_screenshot(name='pic5.png', full_page=True)
            checkin_button = tab.ele('@type=submit')
            if checkin_button:
                checkin_button.click()
                logging.info("签到按钮已点击")
            else:
                raise RuntimeError("未找到签到按钮")

            tab.wait(5)
            tab.get_screenshot(name='pic6.png', full_page=True)
            tab.refresh()
            tab.wait.doc_loaded()
            tab.wait(3)
            logging.info("刷新页面成功")
            tab.get_screenshot(name='pic7.png', full_page=True)
            # 检测签到状态
            checkin_status = tab.ele('text:今日已签到')
            if checkin_status:
                logging.info("签到成功！")
            else:
                logging.info("签到失败！")

    except Exception as e:
        logging.error(f"运行过程中发生错误: {e}")
    finally:
        # 确保浏览器关闭
        logging.info("关闭浏览器...")
        tab.close()
        logging.info("浏览器已关闭")

if __name__ == "__main__":
    main()