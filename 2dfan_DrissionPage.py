import time, os
import logging
from DrissionPage import ChromiumPage
from bypass_captcha import CaptchaBypasser
from DrissionPage import ChromiumOptions

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量
MAX_RETRIES = 3     # 最大重试次数
MAX_LOGIN_ATTEMPTS = 3  # 最大重新登录次数

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

def find_login_input(tab, timeout=20):
    """尝试多种定位策略寻找登录输入框；超时返回 None。"""
    end = time.time() + timeout
    candidate_locators = [
        '@name=login', '@id=login', '@name=email', '@id=email',
        'tag:input[type=email]', 'tag:input[type=text]', 'text:邮箱', 'text:Email'
    ]
    while time.time() < end:
        # 先尝试常用定位器
        for loc in candidate_locators:
            try:
                ele = tab.ele(loc)
                if ele:
                    logging.info(f"找到登录输入元素：{loc}")
                    return ele
            except Exception as ex:
                logging.debug(f"尝试定位 {loc} 时异常: {ex}")
        # 回退：枚举所有 input，打印属性，尝试根据 placeholder/name/id 匹配
        try:
            inputs = tab.eles('tag:input')
            for idx, inp in enumerate(inputs):
                try:
                    attrs = getattr(inp, 'attrs', None)
                    logging.debug(f"input[{idx}] attrs: {attrs}")
                    # 简单尝试：如果 name 或 placeholder 看起来像 email/login 就返回
                    if attrs:
                        name = attrs.get('name','') or attrs.get('id','') or attrs.get('placeholder','')
                        if any(k in name.lower() for k in ('login','email','帐号','帐户','账号','用户名')):
                            logging.info(f"通过属性匹配到输入框: input[{idx}] attrs={attrs}")
                            return inp
                except Exception:
                    continue
        except Exception as ex:
            logging.debug(f"列出 inputs 时异常: {ex}")
        tab.wait(1)
    return None

def find_password_input(tab, timeout=10):
    """在页面上寻找密码输入框，超时返回 None。"""
    end = time.time() + timeout
    candidate = ['@name=password', '@id=password', 'tag:input[type=password]', "text:密码"]
    while time.time() < end:
        for loc in candidate:
            try:
                ele = tab.ele(loc)
                if ele:
                    logging.info(f"找到密码输入元素：{loc}")
                    return ele
            except Exception as ex:
                logging.debug(f"尝试定位 {loc} 时异常: {ex}")
        # 回退：枚举所有 input[type=password]
        try:
            inputs = tab.eles('tag:input')
            for idx, inp in enumerate(inputs):
                try:
                    attrs = getattr(inp, 'attrs', None)
                    if attrs and attrs.get('type','').lower() == 'password':
                        logging.info(f"通过属性匹配到密码框: input[{idx}] attrs={attrs}")
                        return inp
                except Exception:
                    continue
        except Exception as ex:
            logging.debug(f"列出 inputs 时异常: {ex}")
        tab.wait(1)
    return None

def login_process(tab):
    """
    执行登录的输入账号、密码和验证码绕过的流程。
    """
    # 输入账号
    user_email = os.getenv("USER_EMAIL", "")
    if not user_email:
        raise ValueError("环境变量 USER_EMAIL 未设置")
    logging.info(f"输入账号: {user_email}")

    # 更稳健地查找登录输入框
    input_ele = find_login_input(tab, timeout=20)
    if not input_ele:
        logging.error("未能定位登录输入框，保存页面截图以供调试")
        try:
            tab.get_screenshot(name='login_not_found.png', full_page=True)
        except Exception:
            logging.debug("截图失败")
        raise RuntimeError('未找到登录输入框')
    # 找到后输入账号
    input_ele.input(user_email)

    # 输入密码
    user_password = os.getenv("USER_PASSWORD", "")
    if not user_password:
        raise ValueError("环境变量 USER_PASSWORD 未设置")
    logging.info("输入密码")

    pwd_ele = find_password_input(tab, timeout=10)
    if not pwd_ele:
        # 退回到简单定位
        try:
            pwd_ele = tab.ele('@name=password')
        except Exception:
            pwd_ele = None
    if not pwd_ele:
        logging.error("未能定位密码输入框，保存页面截图以供调试")
        try:
            tab.get_screenshot(name='password_not_found.png', full_page=True)
        except Exception:
            logging.debug("截图失败")
        raise RuntimeError('未找到密码输入框')
    pwd_ele.input(user_password)

    # 验证验证码
    tab.wait.eles_loaded("tag:input")
    eles = tab.eles("tag:input")
    button = process_captcha(tab, eles, tag="tag:svg")
    tab.wait.ele_hidden(button)
    logging.info("开始验证")
    tab.wait(3)

    # 初始化验证码绕过程序
    logging.info("初始化验证码绕过程序...")
    captcha_bypasser = CaptchaBypasser()
    logging.info("运行验证码绕过程序...")
    captcha_bypasser.run()

    # 重新抓取输入元素（DOM 可能已变），然后检验是否成功
    tab.wait.eles_loaded("tag:input")
    eles = tab.eles("tag:input")
    button = process_captcha(tab, eles, tag="tag:circle")
    tab.wait.ele_displayed(button)
    logging.info("验证成功")
    tab.wait(2)
    tab.get_screenshot(name='pic1.png', full_page=True)

    # 点击登录按钮
    logging.info("查找并点击登录按钮...")
    login_button = tab.ele('@type=submit')
    if login_button:
        login_button.click()
        logging.info("登录按钮已点击")
    else:
        raise RuntimeError("未找到登录按钮")
    
def main():
    tab = None
    try:
        # 启动浏览器
        logging.info("启动浏览器...")
        co = ChromiumOptions().set_paths(user_data_path=r'/tmp/chrome_user_data').auto_port()
        co.incognito(True)  # 启用无痕模式
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')

        # 是否启用 headless：仅当 HEADLESS 环境变量显式为 true/1/yes 时才启用
        headless_env = os.getenv('HEADLESS', '').lower()
        if headless_env in ('1', 'true', 'yes'):
            logging.info("HEADLESS 环境变量为真，启用 headless 模式")
            co.set_argument('--headless=new')
        else:
            logging.info("未设置 HEADLESS，保留默认（非强制 headless）运行模式")

        # 尝试启动浏览器，失败时回退到新的 user_data_path 并强制 headless
        try:
            tab = ChromiumPage(co)
        except Exception as e:
            logging.warning(f"首次启动浏览器失败：{e}，尝试使用不同的 user_data_path 与 headless 再次启动")
            try:
                co = ChromiumOptions().set_paths(user_data_path=f'/tmp/chrome_user_data_{int(time.time())}').auto_port()
                co.incognito(True)
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-gpu')
                co.set_argument('--disable-dev-shm-usage')
                co.set_argument('--headless=new')
                tab = ChromiumPage(co)
                logging.info("回退方式启动浏览器成功")
            except Exception as e2:
                logging.error(f"回退启动也失败：{e2}")
                raise

        # 跳转到登录页面
        logging.info("跳转到登录页面...")

        # 从环境变量读取登录URL
        LOGIN_URL = os.getenv("LOGIN_URL", "")
        if not LOGIN_URL:
            raise ValueError("环境变量 LOGIN_URL 未设置")
        tab.get(LOGIN_URL)
        logging.info("已跳转到登录页面")

        login_attempts = 0  # 登录尝试计数
        while login_attempts < MAX_LOGIN_ATTEMPTS:
            login_attempts += 1
            logging.info(f"执行登录流程（尝试第 {login_attempts} 次）...")
            
            # 执行登录流程
            try:
                login_process(tab)

                # 检查当前页面URL
                tab.wait.new_tab()
                current_url = tab.url
                logging.info(f"当前页面URL: {current_url}")

                if current_url == "https://2dfan.com/users/sign_in":
                    logging.warning("仍处于登录页面，重新尝试登录...")
                    tab.refresh()
                    tab.wait.doc_loaded()
                    tab.get_screenshot(name='pic_error.png', full_page=True)
                else:
                    logging.info("成功跳转到主页，继续后续操作...")
                    break  # 登录成功，退出循环
            except Exception as e:
                logging.error(f"登录尝试失败: {e}")

        else:
            logging.error("达到最大登录尝试次数，退出程序")
            return

        # 等待页面加载
        tab.wait.eles_loaded("tag:input")
        eles = tab.eles("tag:input")
        logging.info("登录成功")
        tab.get_screenshot(name='pic2.png', full_page=True)

        # 检测签到状态
        checkin_status = tab.ele('text:今日已签到')
        if checkin_status:
            logging.info("今日已签到！")
        else:
            logging.info("未签到，尝试签到...")

            # 再次运行验证码绕过程序
            logging.info("再次运行验证码绕过程序...")
            captcha_bypasser = CaptchaBypasser()
            captcha_bypasser.run()

            # 重新抓取输入元素（DOM 可能已变），然后检验是否成功
            tab.wait.eles_loaded("tag:input")
            eles = tab.eles("tag:input")
            button = process_captcha(tab, eles, tag="tag:circle")
            tab.wait.ele_displayed(button)
            logging.info("验证成功")
            tab.wait(2)
            tab.get_screenshot(name='pic3.png', full_page=True)

            # 更可靠地定位签到按钮（按文本优先，然后回退到 type/class）
            logging.info("查找并点击签到按钮...")
            checkin_button = tab.ele("text:签到") or tab.ele('@type=submit') or tab.ele('css:.checkin, css:.sign-in')
            if not checkin_button:
                # 尝试从所有 submit 元素中选择第一个可见的
                candidates = tab.eles('@type=submit')
                for c in candidates:
                    try:
                        if c.is_displayed():
                            checkin_button = c
                            break
                    except Exception:
                        continue

            if not checkin_button:
                logging.error("未找到签到按钮，保存页面截图以供调试")
                tab.get_screenshot(name='no_checkin_button.png', full_page=True)
                raise RuntimeError("未找到签到按钮")

            # 点击并等待“今日已签到”出现（重试多次）
            success = False
            for attempt in range(3):
                try:
                    checkin_button.click()
                except Exception as e:
                    logging.warning(f"点击签到按钮时出错 (尝试 {attempt+1}): {e}")
                logging.info(f"签到按钮已点击 (尝试 {attempt+1})")
                tab.get_screenshot(name=f'after_checkin_click_{attempt+1}.png', full_page=True)

                # 等待最多 10 秒查看页面上是否出现“今日已签到”
                for _ in range(10):
                    tab.wait(1)
                    if tab.ele('text:今日已签到'):
                        logging.info("检测到签到成功标识")
                        success = True
                        break
                if success:
                    break
                else:
                    logging.warning("未检测到签到成功标识；短暂等待后重试")
                    tab.wait(1)

            if not success:
                logging.info("签到失败，保存调试截图并抛出异常")
                tab.get_screenshot(name='checkin_failed_final.png', full_page=True)
                raise RuntimeError("签到失败!")

    except Exception as e:
        logging.error(f"运行过程中发生错误: {e}")
        with open("failure_flag.txt", "w") as f:
            f.write("Sign-in failed!")
    finally:
        # 确保浏览器关闭
        logging.info("关闭浏览器...")
        try:
            if tab:
                tab.close()
                logging.info("浏览器已关闭")
            else:
                logging.info("tab 未创建，无需关闭浏览器")
        except Exception as e:
            logging.warning(f"关闭浏览器时出错: {e}")

if __name__ == "__main__":
    main()
