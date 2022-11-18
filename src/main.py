from offerup.post import post_offer
from offerup.crawl import crawl

from time import sleep
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
# from utils.utils import android_des_caps
from selenium.common.exceptions import WebDriverException


def android_des_caps(device_name: AnyStr, app_package: AnyStr, main_activity: AnyStr) -> Dict:
    return {
        'platformName': 'Android',
        'appium:deviceName': device_name,
        'appium:appPackage': app_package,
        'appium:automationName': 'UiAutomator2',
        'appium:appActivity': main_activity,
        'appium:ensureWebviewHavepages': "true",
        'appium:nativeWebScreenshot': "true",
        'appium:newCommandTimeout': 3600,
        'appium:connectHardwareKeyboard': "true",
        'appium:noReset': True,
    }

device_name = "192.168.0.163:5555"
app_package = 'com.offerup'
main_activity = 'MainActivity'
driver = webdriver.Remote(
    "http://localhost:4723/wd/hub",
    android_des_caps(
        device_name,
        app_package,
        main_activity
    )
)
driver.wait_activity(main_activity, 5)

# post_offer(
#     driver=driver,
#     title="iPhone X",
#     desc='Best phone in the world',
#     price='420',

# )

crawl(driver)

input("Quit")
driver.quit()
