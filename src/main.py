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
from utils.parallel import MultiprocessTaskRunner
from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, TOP_500_APPS, adb_connect, android_des_caps, find_transport_id


# Multiprocessing Runs

# ips = [
#     '192.168.1.113:5555',
#     # '192.168.1.238:5555',
# ]
# runner = MultiprocessTaskRunner(ips, TOP_500_APPS[:4])
# runner.run()

# Single run


# https://github.com/appium/appium-uiautomator2-driver#driverserver
#   - appium:skipServerInstallation => Improve startup speed if we know UIAutomator is already installed...

# TODO
# Need to identify each device so we can use the correct commands
# So far Pixel 2 and Chromebook Coachz have different View Names
#   - Chromebooks views are obfuscated
# We can use this to get deviceInfo
# https://github.com/appium/appium-uiautomator2-driver#mobile-deviceinfo
# self.driver.execute_script("mobile: scroll", {'direction': 'down'})
# self.driver.execute_script("mobile: acceptAlert", {'buttonLabel': 'Accept'})
# self.driver.execute_script("mobile: dismissAlert", {'buttonLabel': 'Dismiss'})
# self.driver.execute_script("mobile: deviceInfo", {})

# self.driver.execute_script("mobile: activateApp", {appId: "my.app.id"})
    # Activates the given application or launches it if necessary. The action literally simulates clicking the corresponding application icon on the dashboard.
# self.driver.execute_script("mobile: queryAppState", {appId: "my.app.id" })
    # The app is not installed: 0
    # The app is installed and is not running: 1
    # The app is running in background: 3
    # The app is running in foreground: 4



# self.driver.execute_script("mobile: changePermissions", {
#                                   permissions: 'all',
#                                   appPackage: '',
#                                   action: 'allow',
# })
#  mobile: 


# deviceInfo::
# androidId
# manufacturer
# model
# brand
# apiVersion
# platformVersion
# carrierName
# realDisplaySize
# displayDensity
# networks
# locale
# timeZone
# bluetooth


# adb -t 31 shell monkey -p com.netflix.mediaclient -c android.intent.category.LAUNCHER 1

ip = '192.168.1.113:5555'
res = adb_connect(ip)
transport_id = find_transport_id(ip)

driver = webdriver.Remote(
    "http://localhost:4723/wd/hub",
    android_des_caps(
        ip,
        PLAYSTORE_PACKAGE_NAME,
        PLAYSTORE_MAIN_ACT
    )
)
driver.implicitly_wait(5)
driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)

validator = AppValidator(driver, TOP_500_APPS[:5], str(transport_id))
validator.uninstall_multiple()
validator.run()
validator.report.print_report()
print("Putting driver & valdiator")
driver.quit()













# Old Test code, still want...
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

