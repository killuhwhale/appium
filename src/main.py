
"""Main entry point to running search, install, launch, login, reporting.
                                    SILLR
To run this script with the CLI:
Syntax:
python3 main.py [-c --clean] -i --ip <ip-addresses>

Arguments:
    ips: (Required) ip addresses of the DUT.

Example:
    python3 main.py 192.168.1.125 192.168.1.113
"""
import argparse
from multiprocessing import Queue
import sys
from appium import webdriver
from objdetector.yolov8 import YoloV8

from playstore.app_validator import AppValidator
from playstore.facebook_app import  FacebookApp
from playstore.validation_report import ValidationReport
from playstore.validation_report_stats import ValidationReportStats
from serviceManager.appium_service_manager import AppiumServiceManager
from utils.device_utils import Device
from utils.logging_utils import AppListTSV, AppLogger
from utils.parallel import MultiprocessTaskRunner
from utils.utils import BASE_PORT, CONFIG, PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME, V8_WEIGHTS, WEIGHTS, android_des_caps, dev_scrape_start_at_app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="App validation.")
    parser.add_argument("-c", "--clean",
                        help="Clean up appium server..",
                        action='store_true')
    parser.add_argument("-i", "--ips",
                        help="Ip address of DUTs.",
                        default=[], type=list)

    args = parser.parse_args()
    ips = args.ips

    # Multiprocessing Runs
    # if len(ips) == 0:
    #     ips = [
    #         # '710KPMZ0409387',  # Device connected via USB (Pixel 2)
    #         # 'emulator-5554',
    #         # '192.168.1.128:5555', # Kevin ARM ARC-P          Blue,
    #         # '192.168.1.125:5555',  # ARC-R Eve
    #         # '192.168.1.248:5555', # Morphius AMD        ARC-R x86   Yellow,
    #         '192.168.1.238:5555', # Helios   intel      ARC-R x86   RED,
    #         # '192.168.1.149:5555', # Caroline intel      ARC-P x86   Green,
    #         # '192.168.1.113:5555', # CoachZ   snapdragon ARC-P ARM   Green,
    #         # '192.168.1.149:5555', # Careena  AMD        ARC-P x86   Green,
    #     ]
    # print("ips: ", ips)

    # tsv = AppListTSV()  # Create Globally
    # TESTING_APPS = tsv.get_apps()

    # # Dev, choose startin package by name.
    # # starting_app = "com.mojang.minecraftpe"
    # # start_idx = dev_scrape_start_at_app(starting_app, TESTING_APPS)
    # # print(f"{start_idx=} ~ {starting_app=}")
    # # package_names = TESTING_APPS[start_idx: ]

    # # Dev, choose startin package by index.
    # package_names = TESTING_APPS[55:]

    # runner = MultiprocessTaskRunner(ips, package_names)
    # if args.clean:
    #     runner.cleanup_appium_server()
    # if not runner.start_appium_server():
    #     print("Error starting server...")
    #     sys.exit(1)

    # runner.run()
    # runner.print_devices()

    # stats, device = ValidationReportStats.calc(runner.reports_dict)

    # ValidationReportStats.print_stats(stats, device)

    # ValidationReport.print_reports_by_app(runner.reports)

    ####################################
    ##   Single Run
    ####################################

    # ip = "192.168.1.113:5555"
    # ip = '192.168.1.149:5555'
    # ip = "192.168.1.125:5555"
    ip = "192.168.1.238:5555"

    service_manager = AppiumServiceManager([ip])
    if args.clean:
        service_manager.cleanup_services()  # Will exit
    service_manager.start_services()

    device = Device(ip)
    app_logger = AppLogger()
    tsv = AppListTSV()  # Create Globally
    TESTING_APPS = tsv.get_apps()
    package_names = TESTING_APPS[:1]


    print("Creating driver...")
    driver = webdriver.Remote(
        f"http://localhost:{BASE_PORT}/wd/hub",
        android_des_caps(
            ip,
            PLAYSTORE_PACKAGE_NAME,
            PLAYSTORE_MAIN_ACT
        )
    )

    driver.implicitly_wait(5)
    driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)

    fb_handle = FacebookApp(driver, app_logger,  device, BASE_PORT, Queue(),)
    fb_handle.install_and_login()

    validator = AppValidator(
        driver,
        package_names,
        device,
        0,
        Queue(),
        app_logger,
        Queue(),  # Stats
        Queue(),  # Prices
    )
    if not CONFIG.skip_pre_multi_uninstall:
        validator.uninstall_multiple()
    validator.run()

    validator.report.merge(fb_handle.validator.report)
    validator.report.print()

