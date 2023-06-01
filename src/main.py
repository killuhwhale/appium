
"""Main entry point to running search, install, launch, login, reporting.
                                    SILLR
To run this script with the CLI:
Syntax:
python3 main.py [-c --clean] -i --ip <ip-addresses>

Arguments:
    ips: (Required) ip addresses of the DUT.

Example:
    python3 main.py -i 192.168.1.125:5555 192.168.1.113:5555       # Single run
    python3 main.py -i 192.168.1.238:5555 -n 1  # Single run w/ 1 app (starting from beginning of list)
    python3 main.py -p -i 192.168.1.125:5555 192.168.1.113:5555    # Parallel Run
"""
import argparse
from datetime import datetime
from multiprocessing import Queue
from appium import webdriver
import logging
import sys

from playstore.app_validator import AppValidator
from playstore.facebook_app import  FacebookApp
from playstore.validation_report import ValidationReport
from playstore.validation_report_stats import ValidationReportStats
from serviceManager.appium_service_manager import AppiumServiceManager
from utils.device_utils import Device
from utils.logging_utils import AppListTSV, AppLogger, logger
from utils.parallel import MultiprocessTaskRunner
from utils.utils import BASE_PORT, CONFIG, PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME, android_des_caps, dev_scrape_start_at_app
from pympler import asizeof
from uuid import uuid1


def main():
    parser = argparse.ArgumentParser(description="App validation.")
    parser.add_argument("-p", "--parallel",
                        help="Run on multiple devices",
                        action='store_true', default=False)
    parser.add_argument("-c", "--clean",
                        help="Clean up appium server..",
                        action='store_true')
    parser.add_argument("-i", "--ips",
                        help="Ip address of DUTs.",
                        nargs="*",
                        default=[], type=str)
    parser.add_argument("-n", "--num",
                        help="Num of apps to runs.",
                        default=-1, type=int)
    parser.add_argument("-l", "--local",
                        help="Use localhost as base url when sending requests, defaults to GCP.",
                        action='store_true', default=False)


    run_id = uuid1(1337, 42)
    ts = int(datetime.now().timestamp()*1000)
    args = parser.parse_args()
    ips = args.ips
    if args.local:
        CONFIG.base_url = "http://localhost:3000"
    logger.print_log(f"CLI input: {args.parallel=}\n")
    logger.print_log(f"CLI input: {args.local=}\n")
    logger.print_log(f"CLI input: {ips=}\n")
    logger.print_log(f"Config", CONFIG, '\n')
    logger.print_log(f"{run_id=}\n")
    logger.print_log(f"Start time {ts=}\n")

    if (args.parallel):
        # Multiprocessing Runs
        if len(ips) == 0:
            ips = [
                # '710KPMZ0409387',  # Device connected via USB (Pixel 2)
                # 'emulator-5554',
                # '192.168.1.128:5555', # Kevin ARM ARC-P          Blue,
                # '192.168.1.125:5555',  # ARC-R Eve
                # '192.168.1.248:5555', # Morphius AMD        ARC-R x86   Yellow,
                # '192.168.1.238:5555', # Helios   intel      ARC-R x86   RED,
                # '192.168.1.149:5555', # Caroline intel      ARC-P x86   Green,
                # '192.168.1.113:5555', # CoachZ   snapdragon ARC-P ARM   Green,
                # '192.168.1.149:5555', # Careena  AMD        ARC-P x86   Green,
            ]
        logger.print_log("ips: ", ips, '\n')

        tsv = AppListTSV()  # Create Globally
        TESTING_APPS = tsv.get_apps()

        # Dev, choose startin package by name.
        # starting_app = "com.mojang.minecraftpe"
        # start_idx = dev_scrape_start_at_app(starting_app, TESTING_APPS)
        # print(f"{start_idx=} ~ {starting_app=}")
        # package_names = TESTING_APPS[start_idx: ]

        # Dev, choose startin package by index.
        num_apps = args.num if args.num > 0 else len(TESTING_APPS)
        package_names = TESTING_APPS[:num_apps]

        runner = MultiprocessTaskRunner(run_id, ts, ips, package_names)
        runner.run()
        runner.print_devices()

        stats, device = ValidationReportStats.calc(runner.reports_dict)

        ValidationReportStats.print_stats(stats, device)

        ValidationReport.print_reports_by_app(runner.reports)
    else:
        ###################################
        #   Single Run
        ###################################

        # ip = "192.168.1.113:5555"
        # ip = '192.168.1.149:5555'
        # ip = "192.168.1.125:5555"
        # ip = "192.168.1.238:5555"
        # ip = "192.168.1.149:5555"

        ip = ips[0] if not args.clean else ""
        service_manager = AppiumServiceManager([ip])
        if args.clean:
            service_manager.cleanup_services()  # Will exit
        service_manager.start_services()

        device = Device(ip)
        app_logger = AppLogger()
        tsv = AppListTSV()  # Create Globally
        TESTING_APPS = tsv.get_apps()

        num_apps = args.num if args.num > 0 else len(TESTING_APPS)
        package_names = TESTING_APPS[:num_apps]

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

        fb_handle = FacebookApp(driver, app_logger,  device, BASE_PORT, Queue(), run_id, ts)
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
            run_id,
            ts
        )
        if not CONFIG.skip_pre_multi_uninstall:
            validator.uninstall_multiple()
        validator.run()

        print(f"Site of validation report dict: {(asizeof.asizeof(validator.report.report) / 1000.0):.2f} KB")
        validator.report.merge(fb_handle.validator.report)
        validator.report.print()


if __name__ == "__main__":
    try:
        logging.basicConfig(filename='crash.log', filemode='w', level=logging.ERROR)
        main()
    except Exception as e:
        logging.critical("main crashed")

