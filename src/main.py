from time import sleep
from appium import webdriver
import sys

from playstore.playstore import AppValidator
from utils.parallel import MultiprocessTaskRunner
from utils.utils import (PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME,
    TOP_500_APPS, Device, android_des_caps,
    lazy_start_appium_server, stop_appium_server)

# Starts Appium Server.
# python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555


weights = 'notebooks/yolov5/runs/train/exp007/weights/best_309.pt'
weights = 'notebooks/yolov5/runs/train/exp4/weights/best.pt'  # Lastest RoboFlow Model V1
weights = 'notebooks/yolov5/runs/train/exp6/weights/best.pt'  # Lastest RoboFlow Model V2
weights = 'notebooks/yolov5/runs/train/exp7/weights/best.pt'  # Lastest RoboFlow Model V3

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

    # service = lazy_start_appium_server()

    # runner = MultiprocessTaskRunner(ips, TOP_500_APPS[:1] )
    # runner.run()


    ###################################
    #   Single run
    ###################################

    # ip = '192.168.1.128:5555' # ARC-P Kevin ARM 32-bit
    # ip = '192.168.1.125:5555' # ARC-R Eve
    # ip = 'emulator-5554' # ARC-R
    # ip = '710KPMZ0409387' # ARC-R Pixel 2
    # ip = '192.168.1.149:5555' # ARC-P Caroline,
    # ip = '192.168.1.248:5555' # ARC-R Morphius,
    # ip = '192.168.1.:5555' # ARC-P Krane,
    # ip = '192.168.1.137:5555' # ARC-R Kohaku,
    ip = '192.168.1.238:5555' # ARC-R Helios,
    # ip = '192.168.1.113:5555' # ARC-P CoachZ

    service = lazy_start_appium_server()
    device = Device(ip)
    # res = adb_connect(ip)
    # transport_id = find_transport_id(ip)
    # version = get_arc_version(transport_id)
    # is_emu = is_emulator(transport_id)
    # device_name = get_device_name(transport_id)

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
    sleep(3)  # Wait for playstore to load, there is an animation that delays the text from showing immediately which cause the search to fail (on first launch i think...)

    validator = AppValidator(
        driver,
        TOP_500_APPS[1:2],
        device,
        weights
        )
    input("Pause....")
    validator.uninstall_multiple()
    validator.run()
    validator.report.print_report()
    driver.quit()

    ###################################
    #   End Single run
    ###################################



    print("Stopping App server")
    stop_appium_server(service)

