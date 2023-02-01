from appium import webdriver
import sys

from playstore.playstore import AppValidator
from utils.parallel import MultiprocessTaskRunner
from utils.utils import (PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME,
    TOP_500_APPS, adb_connect, android_des_caps, find_template, find_transport_id, gather_app_info, get_apk, get_arc_version, lazy_start_appium_server, stop_appium_server)

# Starts Appium Server.
# python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555
if __name__ == "__main__":
    ips = sys.argv[1:]

    # # Multiprocessing Runs
    # if len(ips) == 0:
    #     ips = [
    #         # '710KPMZ0409387',  # Device connected via USB (Pixel 2)
    #         # 'emulator-5554',
    #         # '192.168.1.248:5555', # Morphius AMD ARC-P        Yellow,
    #         # '192.168.1.128:5555',  # Kevin ARM ARC-p          Blue,
    #         # '192.168.1.113:5555', # CoachZ snapdragon ARC-P   Green,
    #         '192.168.1.238:5555',  # Helios x86 intel ARC-R   RED,

    #     ]
    # print("ips: ", ips)

    # lazy_start_appium_server()

    # runner = MultiprocessTaskRunner(ips, TOP_500_APPS[:1] )
    # runner.run()


    ###################################
    #   Single run
    ###################################

    # ip = '710KPMZ0409387' # ARC-R
    # ip = '192.168.1.238:5555' # ARC-R Helios, Failing on install step ##*#*#*#*#*#**#*##*
    # ip = 'emulator-5554' # ARC-R
    ip = '192.168.1.113:5555' # ARC-P

    res = adb_connect(ip)
    transport_id = find_transport_id(ip)
    version = get_arc_version(transport_id)



    lazy_start_appium_server()
    print("Creating driver...")
    driver = webdriver.Remote(
        "http://0.0.0.0:4723/wd/hub",
        android_des_caps(
            ip,
            PLAYSTORE_PACKAGE_NAME,
            PLAYSTORE_MAIN_ACT
        )
    )
    driver.implicitly_wait(5)
    driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)


    validator = AppValidator(driver, TOP_500_APPS[:50], transport_id, version, ip)
    validator.uninstall_multiple()
    validator.run()
    validator.report.print_report()
    driver.quit()

    print("Stopping App server")
    stop_appium_server()










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