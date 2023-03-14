from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from time import sleep
import sys

from playstore.playstore import AppValidator, FacebookApp, ValidationReport
from utils.parallel import MultiprocessTaskRunner
from utils.utils import (PLAYSTORE_MAIN_ACT, PLAYSTORE_PACKAGE_NAME,
    TSV, Device, android_des_caps, dev_scrape_start_at_app,
    lazy_start_appium_server, p_blue, p_green, p_red, p_yellow)

# Starts Appium Server.
# python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555

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
            # '192.168.1.113:5555', # CoachZ snapdragon ARC-P   Green,
            '192.168.1.125:5555',  # ARC-R Eve
        ]
    print("ips: ", ips)


    tsv = TSV()  # Create Globally
    TESTING_APPS = tsv.get_apps()


    runner = MultiprocessTaskRunner(ips, TESTING_APPS[1:2] )
    runner.run()

    tsv.update_list(runner.update_app_names)
    tsv.export_bad_apps(runner.bad_apps)
    tsv.write_failed_apps(runner.failed_apps)
    runner.print_devices()
    ValidationReport.print_reports_by_app(runner.get_final_reports())


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
    # ip = '192.168.1.238:5555' # ARC-R Helios,
    # ip = '192.168.1.113:5555' # ARC-P CoachZ


    # tsv = TSV()  # Create Globally
    # TESTING_APPS = tsv.get_apps()
    # name_updates = {}
    # bad_apps = {}



    # service = lazy_start_appium_server(4723)
    # device = Device(ip)

    # print("Creating driver...")
    # driver = webdriver.Remote(
    #     "http://0.0.0.0:4723/wd/hub",
    #     android_des_caps(
    #         ip,
    #         PLAYSTORE_PACKAGE_NAME,
    #         PLAYSTORE_MAIN_ACT
    #     )
    # )
    # driver.implicitly_wait(5)
    # driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)
    # sleep(3)  # Wait for playstore to load, there is an animation that delays the text from showing immediately which cause the search to fail (on first launch i think...)

    # fb_handle = FacebookApp(driver, device, 0)
    # fb_handle.install_and_login()

    # starting_app = "jp.co.yahoo.gyao.android.app"
    # starting_app = "com.facebook.orca"
    # starting_app = "com.showmax.app"
    # starting_app = "com.softinit.iquitos.whatswebscan"
    # starting_app = "com.facebook.orca"
    # starting_app = "com.ss.android.ugc.trill"

    # start_idx = dev_scrape_start_at_app(starting_app, TESTING_APPS)
    # print(f"{start_idx=} ~ {starting_app=}")

    # validator = AppValidator(
    #     driver,
    #     # TOP_500_APPS[start_idx: start_idx + 1],
    #     TESTING_APPS[start_idx: start_idx + 1],
    #     device,
    #     0
    # )

    # validator.uninstall_multiple()
    # validator.run()



    # name_updates.update(validator.update_app_names)  # Iterate of all App validation instances and add here.
    # bad_apps.update(validator.bad_apps)

    # tsv.update_list(name_updates)
    # tsv.export_bad_apps(bad_apps)
    # tsv.write_failed_apps(validator.failed_apps)

    # validator.report.merge(fb_handle.validator.report)
    # validator.report.print()
    # driver.quit()
    # print("Stopping App server")
    # service.stop()


    ###################################
    #   End Single run
    ###################################






