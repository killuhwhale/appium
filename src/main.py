
"""Main entry point to running search, install, launch, login, reporting.
                                    SILLR

Tests apps located in app_list.tsv which is a 2 column tsv file with columns
app name and package name.

To run this script with the CLI:
Syntax:
python3 cpu.py [-d <time-in-seconds>] [-o <output-file>] package_id

Arguments:
    ips: (Required) ip addresses of the DUT.
   TODO() duration or d: (optional) Duration of time we run this script. By default
                the duration is 1 day.

Example:
    python3 main.py 192.168.1.125 192.168.1.113
"""
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from time import sleep
import sys

from playstore.playstore import AppValidator, FacebookApp, ValidationReport
from utils.parallel import MultiprocessTaskRunner
from utils.utils import (PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME,
    AppListTSV, Device, android_des_caps, dev_scrape_start_at_app,
    lazy_start_appium_server, p_blue, p_green, p_red, p_yellow)


if __name__ == "__main__":

    ips = sys.argv[1:]

    # Multiprocessing Runs
    if len(ips) == 0:
        ips = [
            # '710KPMZ0409387',  # Device connected via USB (Pixel 2)
            # 'emulator-5554',
            # '192.168.1.248:5555', # Morphius AMD ARC-P        Yellow,
            # '192.168.1.128:5555',  # Kevin ARM ARC-p          Blue,
            # '192.168.1.238:5555', # Helios x86 intel ARC-R   RED,
            '192.168.1.113:5555', # CoachZ snapdragon ARC-P   Green,
            '192.168.1.125:5555',  # ARC-R Eve
        ]
    print("ips: ", ips)


    tsv = AppListTSV()  # Create Globally
    TESTING_APPS = tsv.get_apps()

    # Dev, choose startin package by name.
    # starting_app = "jp.co.yahoo.gyao.android.app"
    # starting_app = "com.facebook.orca"
    # starting_app = "com.showmax.app"
    # starting_app = "com.softinit.iquitos.whatswebscan"
    # starting_app = "com.facebook.orca"
    # starting_app = "com.ss.android.ugc.trill"
    # starting_app = "com.picsart.studio"
    # start_idx = dev_scrape_start_at_app(starting_app, TESTING_APPS)
    # print(f"{start_idx=} ~ {starting_app=}")
    # package_names = TESTING_APPS[start_idx: start_idx + 1]

    # Dev, choose startin package by index.
    package_names = TESTING_APPS[0:3]

    runner = MultiprocessTaskRunner(ips, package_names)
    runner.run()
    runner.print_devices()

    report_stats = runner.get_final_report_stats()
    report_stats.print_stats()

    # tsv.update_list(report_stats.stats['all_misnamed'])
    # tsv.export_bad_apps(report_stats.stats['all_invalid'])
    ValidationReport.print_reports_by_app(report_stats.reports)





