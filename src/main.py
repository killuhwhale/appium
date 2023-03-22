
"""Main entry point to running search, install, launch, login, reporting.
                                    SILLR

Uses file in home directory:
1. app_list.tsv
    - List of appnames, package names to test.

Produces files in home directory:
1. bad_app_list.tsv
    - Invalid packages
2. failed_apps_live.tsv
    - Report of failed apps
3. passed_apps_live.tsv
    - Report of passed apps
4. latest_stat_report.tsv
    - Numerical summary of reports
5. latest_report.txt
    - Logs + Summary of run

To run this script with the CLI:
Syntax:
python3 cpu.py [-d <time-in-seconds>] [-o <output-file>] package_id

Arguments:
    ips: (Required) ip addresses of the DUT.

Example:
    python3 main.py 192.168.1.125 192.168.1.113
"""
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from time import sleep
import sys

from playstore.playstore import AppValidator, FacebookApp, ValidationReport
from utils.parallel import MultiprocessTaskRunner, ValidationReportStats
from utils.utils import AppListTSV


if __name__ == "__main__":
    ips = sys.argv[1:]
    # Multiprocessing Runs
    if len(ips) == 0:
        ips = [
            # '710KPMZ0409387',  # Device connected via USB (Pixel 2)
            # 'emulator-5554',
            # '192.168.1.248:5555', # Morphius AMD ARC-P        Yellow,
            # '192.168.1.128:5555',  # Kevin ARM ARC-p          Blue,
            '192.168.1.238:5555', # Helios x86 intel ARC-R   RED,
            '192.168.1.113:5555', # CoachZ snapdragon ARC-P   Green,
            '192.168.1.125:5555',  # ARC-R Eve
        ]
    print("ips: ", ips)

    tsv = AppListTSV()  # Create Globally
    TESTING_APPS = tsv.get_apps()

    # Dev, choose startin package by name.
    # starting_app = "com.picsart.studio"
    # start_idx = dev_scrape_start_at_app(starting_app, TESTING_APPS)
    # print(f"{start_idx=} ~ {starting_app=}")
    # package_names = TESTING_APPS[start_idx: start_idx + 1]

    # Dev, choose startin package by index.
    package_names = TESTING_APPS[:1]

    runner = MultiprocessTaskRunner(ips, package_names)
    runner.run()
    runner.print_devices()



    # tsv.update_list(report_stats.stats['all_misnamed'])
    # tsv.export_bad_apps(report_stats.stats['all_invalid'])
    stats, device = ValidationReportStats.calc(runner.reports_dict)
    ValidationReportStats.print_stats(stats, device)

    ValidationReport.print_reports_by_app(runner.reports)





