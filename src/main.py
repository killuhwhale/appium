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

