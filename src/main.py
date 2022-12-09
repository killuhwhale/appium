from offerup.post import post_offer
# from offerup.crawl import crawl

from playstore.playstore import discover_and_install, open_playstore, is_open, is_installed


from time import sleep
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
# from utils.utils import android_des_caps
from selenium.common.exceptions import WebDriverException
from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT

# cd /opt/android-studio/bin && ./studio.sh

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

# device_name = "192.168.0.163:5555"
device_name = "emulator-5554"
app_package = PLAYSTORE_PACKAGE_NAME
main_activity = 'MainActivity'
install_package_name = 'com.offerup'
app_title = 'OfferUp: Buy. Sell. Letgo.'
driver = webdriver.Remote(
    "http://localhost:4723/wd/hub",
    android_des_caps(
        device_name,
        app_package,
        PLAYSTORE_MAIN_ACT
    )
)
driver.wait_activity(main_activity, 5)
driver.implicitly_wait(10)


open_playstore()
sleep(2)
discover_and_install(driver, app_title, install_package_name)









# categories = {
#     'cell phone': 0,
#     'computer accessories': 1,
# }
# cooler = {
#     'title': "AIO 240mm CPU liquid cooler",
#     'desc': "TISHRIC Water Cooler CPU Fan 120 240 360mm RGB Cooling Fan Heatsink Intel LGA 2011/1151/AM3+/AMD AM4 Processor Cooler Radiator",
#     'price': "70",
#     'folder': 'cooler1',
#     'category': categories['cell phone'],
# }

# rack = {
#     'title': "Weightlifting rack and bench",
#     'desc': "ER KANG Multi-Functional Barbell Rack, 800 LBS Capacity Fitness Adjustable Power Cage Dip Stand Squat Power Rack for Home Gym, Weight Lifting, Bench OG price $235 + $ 90 ",
#     'price': "250",
#     'folder': 'rack',
#     'category': categories['computer accessories'],
# }


# post_offer(
#     driver=driver,
#     **rack
# )


# post_offer(
#     driver=driver,
#     title="Cooler",
#     desc='da coldest',
#     price='75',

# )

# crawl(driver)

input("Quit")
driver.quit()
