# from offerup.post import post_offer
# from offerup.crawl import crawl
from playstore.playstore import AppValidator
from launcher.launcher import Launcher
from time import sleep
# from utils.utils import android_des_caps
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, TOP_500_APPS

# Dev
# Defined here for easy copy-paste into terminal to start an interactive session.
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

# Driver target: App to control via Appium 
app_package = PLAYSTORE_PACKAGE_NAME
main_activity = PLAYSTORE_MAIN_ACT

# Prerequisites
# Chromebook turned on, logged in, Linux Started, Appium Server Running pointing to the correct IP Address from Linux, Port Forwarding turned on

# We can create drivers for multiple hosts...
# We can run the client from a more powerful machine and have other
# chromebooks running APPIUM server
# We then use those chromebook's local IPs as the executor address and the adb device name would be consisten most  likely
# The chromebooks used would be the machines we would want to test on and verify with.
# The client could manage all these chroomebooks and run object detection.


# TODO create architecture to create multiple Drivers and start a job for each one.
# Currently the code represents  single Driver and the job to do.
# We could simply package this into a class ClientDriver and then run these in parallel

# For ip in machine_ips:
#    run_thread(ClientDriver, ip, package_names_to_test)


driver = webdriver.Remote(
    "http://localhost:4723/wd/hub",
    android_des_caps(
        device_name,
        app_package,
        main_activity
    )
)
driver.implicitly_wait(5)
driver.wait_activity(main_activity, 5)


# package_names_to_test = [
#     ['OfferUp: Buy. Sell. Letgo.', 'com.offerup'],
#     ['Spotify: Music, Podcasts, Lit', 'com.spotify.music'],
# ]

start = 2
end = 10
package_names_to_test = TOP_500_APPS[start: end]

validator = AppValidator(driver, package_names_to_test)
validator.uninstall_multiple()
validator.run()
validator.report.print_report()
# launcher = Launcher(package_names_to_test)

# launcher.run()

input("Quit")
try:
    driver.quit()
except Exception as e:
    pass
# Test code
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

