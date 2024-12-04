"Hansimov/captcha-bypass"

import cv2
import pyautogui
import random
import time
from mss import mss
from pathlib import Path
from PIL import Image, ImageGrab
import logging
class ImageMatcher:
    def __init__(self, source_image_path, template_image_path):
        self.source_image = cv2.imread(str(source_image_path))
        self.template_image = cv2.imread(str(template_image_path))
        self.detected_image_path = source_image_path.parent / "screenshot_detected.png"

    def match(self):
        res = cv2.matchTemplate(
            self.source_image, self.template_image, cv2.TM_CCOEFF_NORMED
        )
        _, _, _, match_location = cv2.minMaxLoc(res)
        match_left = match_location[0]
        match_top = match_location[1]
        match_right = match_location[0] + self.template_image.shape[1]
        match_bottom = match_location[1] + self.template_image.shape[0]
        match_region = (match_left, match_top, match_right, match_bottom)

        self.match_region = match_region
        return match_region

    def draw_rectangle(self):
        cv2.rectangle(
            img=self.source_image,
            pt1=self.match_region[:2],
            pt2=self.match_region[2:],
            color=(0, 255, 0),
            thickness=2,
        )
        cv2.imwrite(str(self.detected_image_path), self.source_image)
    
    def accuracy(self):
        res = cv2.matchTemplate(
            self.source_image, self.template_image, cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val


class CaptchaBypasser:
    def __init__(self):
        self.captcha_image_path = (
            Path(__file__).parent / "captcha-verify-you-are-human-eg.png"  # 自动部署图片加eg，本地不加
        )
        self.screen_shot_image_path = Path(__file__).parent / "screenshot.png"

    def get_screen_shots(self):
        ImageGrab.grab(all_screens=True).save(self.screen_shot_image_path)

    def get_captcha_location(self):
        with mss() as sct:
            all_monitor = sct.monitors[0]
            monitor_left_offset = all_monitor["left"]
            monitor_top_offset = all_monitor["top"]

        image_matcher = ImageMatcher(
            source_image_path=self.screen_shot_image_path,
            template_image_path=self.captcha_image_path,
        )

        match_region = image_matcher.match()
        image_matcher.draw_rectangle()
        logging.info("准确度：%s", image_matcher.accuracy())
        match_region_in_monitor = (
            match_region[0] + monitor_left_offset,
            match_region[1] + monitor_top_offset,
            match_region[2] + monitor_left_offset,
            match_region[3] + monitor_top_offset,
        )
        checkbox_center = (
            int(match_region_in_monitor[0] + 40), #本地60 自动部署40
            int((match_region_in_monitor[1] + match_region_in_monitor[3]) / 2),
        )

        # 该处画点并保存图片
        cv2.circle(
            img=image_matcher.source_image,
            center=checkbox_center,
            radius=2,
            color=(0, 0, 255),
            thickness=-1,
        )
        cv2.imwrite(str(image_matcher.detected_image_path), image_matcher.source_image)
        return checkbox_center

    def click_target_checkbox(self):
        captcha_checkbox_center = self.get_captcha_location()
        pyautogui.moveTo(*captcha_checkbox_center)
        pyautogui.click()

    def run(self):
        self.get_screen_shots()
        self.get_captcha_location()
        self.click_target_checkbox()


if __name__ == "__main__":
    captcha_bypasser = CaptchaBypasser()
    captcha_bypasser.run()
