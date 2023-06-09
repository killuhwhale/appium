from datetime import datetime
from multiprocessing import Queue
from time import sleep
from typing import Dict, List

import __main__
import requests
from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from google.cloud import storage
from pympler import asizeof
import json

from playstore.app_installer import AppInstaller, AppInstallerResult
from playstore.app_launcher import AppLauncher
from playstore.app_login import AppLogin
from playstore.app_login_results import AppLoginResults
from playstore.validation_report import ValidationReport
from utils.app_utils import (AppData, AppInfo, close_app, close_save_password_dialog,
                             get_cur_activty, get_views, open_app,
                             uninstall_app)
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import AppLogger, get_color_printer
from utils.post_to_firebase import post_to_firebase
from utils.utils import CONFIG, PLAYSTORE_PACKAGE_NAME, AppStatus

# Instantiates a client
storage_client = storage.Client()


class AppValidator:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.
    '''
    def __init__(
            self,
            driver: Remote,
            package_names: List[List[str]],
            device: Device,
            instance_num: int,
            app_list_queue: Queue,
            app_logger: AppLogger,
            stats_queue: Queue,
            price_queue: Queue,
            run_id: str,
            ts: int,
        ):
        self.__run_id = run_id
        self.__ts = ts
        self.__driver = driver
        self.__device = device
        self.__transport_id = device.info.transport_id
        self.__report = ValidationReport(device)
        self.__err_detector = ErrorDetector(device.info, self.__device.info.arc_version)
        self.__app_list_queue = app_list_queue
        self.__stats_queue = stats_queue
        self.__price_queue = price_queue
        self.__app_logger = app_logger
        self.__package_names = package_names  # List of packages to test as [app_title, app_package_name]
        self.__instance_num = instance_num
        self.dev_ss_count = 8
        self.__dprinter = self.__dprint

    def __dprint(self, *args):
        get_color_printer(self.__instance_num)(self.__report.report_title, *args)

    @property
    def report(self):
        return self.__report

    def uninstall_multiple(self):
        for app_info in self.__package_names:
            package_name = app_info[1]
            uninstall_app(package_name, self.__transport_id)


    def __upload_img(self, source_file_name: str, package_name: str, hist_step: int):
        # The ID of your GCS bucket
        bucket_name = "appval-387223.appspot.com"
        # The path to your file to upload
        # source_file_name = "local/path/to/file"
        # The ID of your GCS object
        # destination_blob_name = "storage-object-name"
        destination_blob_name = f"appRuns/{self.__run_id}/{self.__report.report_title}/{package_name}/{hist_step}"
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request to upload is aborted if the object's
        # generation number does not match your precondition. For a destination
        # object that does not yet exist, set the if_generation_match precondition to 0.
        # If the destination object already exists in your bucket, set instead a
        # generation-match precondition using its generation number.
        generation_match_precondition = 0

        blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)
        return destination_blob_name

    def __upload_images_to_firebase_storage(self, history: List[Dict[str, str]], package_name: str):
        '''Takes an apps full history and uploads each image to Firebase storage.'''

        i  = 0
        while i < len(history):
            hist = history[i]
            # while not upload_img() and attemps > 0:
            print("Upload hist img function here", hist['img'])
            destination_blob_name = self.__upload_img(hist['img'], package_name, i)
            if not destination_blob_name:
                destination_blob_name = self.__upload_img(hist['img'], package_name, i)

            history[i]['img'] = destination_blob_name
            i += 1



    def __cleanup_run(self, app_package_name: str):
        self.__dprint(f"Cleaning up {app_package_name}")
        status_obj = self.__report.get_status_obj_by_app(app_package_name)
        #  Log results to tsv File
        # When updating this, AppLogger.headers must also be updated.
        device_build_info = f"{self.__device.info.arc_build},{self.__device.info.channel},{self.__device.info.arc_version}"
        app_run_time = datetime.now()
        app_run_ts = int(app_run_time.timestamp()*1000) # Firebase needs a date
        app_info: AppData = self.__report.get_app_info(app_package_name)
        print("App info post: ", type(app_info), app_info )
        self.__upload_images_to_firebase_storage(status_obj['history'], status_obj['package_name'])


        post_to_firebase({
            'status': status_obj['status'],
            'package_name': status_obj['package_name'],
            'name': status_obj['name'],
            'app_type': app_info.app_type.value,
            'app_version': f"{app_info.versionName} - {app_info.versionCode}",
            'report_title': status_obj['report_title'],
            'run_id': str(self.__run_id),
            'run_ts': self.__ts,
            'build': device_build_info,
            'timestamp': app_run_ts,  # Log string instead of ts
            'history': str(status_obj['history']),
            'logs': status_obj['logs'],
        })


        self.__app_logger.log(
            status_obj['status'],
            status_obj['package_name'],
            status_obj['name'],
            status_obj['status'],
            app_info.app_type,
            f"{app_info.versionName} - {app_info.versionCode}",
            status_obj['report_title'],
            self.__run_id,
            self.__ts,
            device_build_info,
            app_run_time.strftime("%A, %B %d, %Y %I:%M:%S %p"),  # Log string instead of ts
            status_obj['history'],
            status_obj['logs'],
        )

        self.__stats_queue.put(status_obj)
        close_app(app_package_name, self.__transport_id)
        if not CONFIG.skip_post_uninstall:
            uninstall_app(app_package_name, self.__transport_id)  # (save space)
        # check to close Android diaglog asking to save password
        close_save_password_dialog(self.__driver)

        open_app(PLAYSTORE_PACKAGE_NAME, self.__transport_id, self.__driver, self.__device.info.arc_version)
        self.__driver.orientation = 'PORTRAIT'

    def __switch_crash_type(self, crashType: CrashTypes):
        ''' Switch control to map CrashTypes to ValidationReport status

        '''
        if(crashType == CrashTypes.WIN_DEATH):
            return AppStatus.CRASH_WIN_DEATH
        elif(crashType == CrashTypes.FORCE_RM_ACT_RECORD):
            return AppStatus.CRASH_FORCE_RM_ACT_RECORD
        elif(crashType == CrashTypes.ANR):
            return AppStatus.CRASH_ANR
        elif(crashType == CrashTypes.FDEBUG_CRASH):
            return AppStatus.CRASH_FDEBUG_CRASH
        elif(crashType == CrashTypes.FATAL_EXCEPTION):
            return AppStatus.CRASH_FATAL_EXCEPTION
        else:
            AppStatus.FAIL

    def __check_crash(self, package_name: str) -> bool:
        ''' Updates report if crash is detected.

            Args:
                - package_name: Name of the package to check.

            Returns:
                - True if a crash was detected.
        '''
        print("checkinbg for crash in app_val")
        errors = self.__err_detector.check_crash()
        # CrashType, crashed_act, msg = self.__err_detector.check_crash()
        if(not CrashTypes.SUCCESS in errors):
            self.__report.add_logs(package_name, self.__err_detector.logs.replace('\t', '').replace('\n', ''))
            all_errors_msg = []
            report_status_crash_type = None  # Used to catch mutiple errors and only report highest precedence
            for key, val in errors.items():
                crash_type, crashed_act, msg = val
                if not report_status_crash_type:
                    report_status_crash_type = crash_type
                elif report_status_crash_type == CrashTypes.WIN_DEATH and crash_type == CrashTypes.FDEBUG_CRASH:
                    report_status_crash_type = crash_type
                elif report_status_crash_type == CrashTypes.WIN_DEATH and crash_type == CrashTypes.FATAL_EXCEPTION:
                    report_status_crash_type = crash_type

                all_errors_msg.append(crash_type.value)
                self.__report.add_history(package_name, f"{crash_type.value}: {crashed_act} - {msg}", self.__driver)

            self.__report.update_status(package_name, self.__switch_crash_type(report_status_crash_type))
            print("\n\n Found error returning True")
            return True
        return False

    def __scrape_dev_test_image(self, package_name: str):
        try:
            self.__driver.get_screenshot_as_file(
                f"/home/killuh/ws_p38/appium/src/notebooks/yolo_images/scraped_images/{package_name}_{self.dev_ss_count}.png"
            )
            self.dev_ss_count += 1
        except Exception as error:
            self.__dprint("Error w/ dev ss: ", error)

    def __update_report_logged_in_status(self, package_name: str, login_results: AppLoginResults):
        print(f"Updating report with: {login_results.__dict__=}")
        self.__report.update_status_login(package_name, login_results)


    def __dev_SS_loop(self, package_name: str):
        ''' Loop that pauses on input allowing to take multiple screenshots
                after manually changing app state.
        '''
        ans = ''
        while not (ans == 'q'):
            ans = input("Take your screen shots bro...")
            self.__dprint(f"{ans=}, {(not ans == 'q')}")
            if not (ans == 'q'):
                self.__dprint("Taking SS")
                print(f"Current act: ", self.__driver.current_activity)
                # self.__scrape_dev_test_image(package_name)
            else:
                self.__dprint("Quit from SS")

    def __check_pop_ups(self, app_package_name: str):
        '''Checks for pop ups after opening an app.'''
        try:
            content_desc = f'''
                    new UiSelector().className("android.widget.Button").text("I ACCEPT")
                '''
            self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()

        except Exception as err:
            print("Didnt find pop up")


    def __process_app(self, app_title:str, app_package_name: str):
        self.__report.add_app(app_package_name, app_title)
        self.__err_detector.update_package_name(app_package_name)

        # Install
        if not CONFIG.skip_install:
            installer = AppInstaller(self.__driver, self.__device, self.__dprinter)
            install_result: AppInstallerResult = installer.discover_and_install(app_title, app_package_name)
            self.__report.add_history(app_package_name, "App install successfull." if install_result.status.value > 0 else "Failed to install.", self.__driver)
            if install_result.price:
                self.__price_queue.put((app_title, app_package_name, install_result.price,))
                return self.__report.update_status(app_package_name, AppStatus.NEEDS_PRICE)
            elif not install_result.installed:
                return self.__report.update_status(app_package_name, install_result.status)



        # Lauch App
        if not CONFIG.skip_launch:
            launcher = AppLauncher(self.__device, self.__driver, self.__app_list_queue, self.__dprinter)
            app_did_open  = launcher.check_open_app(app_title, app_package_name)
            if not app_did_open:
                hist_msg = "failed to open"
                self.__check_crash(app_package_name)
                self.__report.add_history(app_package_name, hist_msg, self.__driver)
                return self.__report.update_status(app_package_name, AppStatus.FAILED_TO_LAUNCH)


            sleep(5)
            if self.__check_crash(app_package_name):
                return
            self.__report.update_status(app_package_name, AppStatus.PASS)
            # App is needs to be gathered after app is open since it looks for a surface to check if an app is a game.
            info: AppData = AppInfo(self.__transport_id, app_package_name, self.__dprinter).info()
            print(f"{info=}")
            self.__report.update_app_info(app_package_name, info)

            # Close any pop ups after opening app
            self.__check_pop_ups(app_package_name)


        # self.__dev_SS_loop(app_package_name)

        # Now app is installed and launched...
        if not CONFIG.skip_login:
            login_module = AppLogin(self.__driver, self.__device, self.__report, self.__err_detector, self.__dprinter)
            login_results: AppLoginResults = login_module.login(app_title, app_package_name, info)
            print(f"{login_results.__dict__=}")
            as_byte_num = login_results.to_byte()
            print(f"{as_byte_num=}")
            new_result_obj = AppLoginResults.from_byte(as_byte_num)
            print(f"{new_result_obj.__dict__=}")

            print(f"{login_results=}")
            # logged_in_msg = "Logged in." if any(list(login_results.__dict__.values())[::2]) else "Not logged in."
            self.__report.update_status(app_package_name, AppStatus.PASS)
            self.__update_report_logged_in_status(app_package_name, login_results)

            if self.__check_crash(app_package_name):
                return

    ##  Main Loop
    def run(self):
        '''
            Main loop of the Playstore class, starts the cycle of discovering,
            installing, logging in and uninstalling each app from self.__package_names.

            It ensures that the playstore is open at the beginning and that
            the device orientation is returned to portrait.
        '''

        self.__driver.orientation = 'PORTRAIT'
        i = 0
        for app_title, app_package_name in self.__package_names:
            # Allows for recursive call to retest an app.
            self.__process_app(app_title, app_package_name)
            print(f"Size of validation report dict ({i}): {(asizeof.asizeof(self.__report.report) / 1000.0):.2f} KB")
            i += 1
            self.__cleanup_run(app_package_name)

if __name__ == "__main__":
    pass