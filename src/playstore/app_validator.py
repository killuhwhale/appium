from multiprocessing import Queue
from typing import List
import __main__
from appium.webdriver import Remote
from playstore.app_installer import AppInstaller, AppInstallerResult
from playstore.app_login import AppLogin
from playstore.app_launcher import AppLauncher
from playstore.validation_report import ValidationReport
from utils.app_utils import AppInfo, close_app, open_app, uninstall_app
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import AppLogger, get_color_printer
from utils.utils import PLAYSTORE_PACKAGE_NAME

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
        ):
        self.__driver = driver
        self.__device = device
        self.__transport_id = device.info.transport_id
        self.__report = ValidationReport(device)
        self.__err_detector = ErrorDetector(self.__transport_id, self.__device.info.arc_version)
        self.__app_list_queue = app_list_queue
        self.__stats_queue = stats_queue
        self.__price_queue = price_queue
        self.__app_logger = app_logger
        self.__package_names = package_names  # List of packages to test as [app_title, app_package_name]
        self.__instance_num = instance_num
        self.dev_ss_count = 8
        self.__dprint = get_color_printer(instance_num)

    @property
    def report(self):
        return self.__report

    def uninstall_multiple(self):
        for app_info in self.__package_names:
            package_name = app_info[1]
            uninstall_app(package_name, self.__transport_id)

    def __cleanup_run(self, app_package_name: str):
        self.__dprint(f"Cleaning up {app_package_name}")
        status_obj = self.__report.get_status_obj_by_app(app_package_name)
        '''
            'status': -1,
            'package_name': '',
            'new_name': "",
            'invalid': False,
            'reason': "",
            'name': "",
            'report_title': "",
            'history': [],
            'logs', ''
        '''
        self.__app_logger.log(
            status_obj['status'],
            status_obj['package_name'],
            status_obj['name'],
            status_obj['report_title'],
            status_obj['reason'],
            status_obj['new_name'],
            status_obj['invalid'],
            status_obj['history'],
            status_obj['logs'],
        )

        self.__stats_queue.put(status_obj)
        close_app(app_package_name, self.__transport_id)
        uninstall_app(app_package_name, self.__transport_id)  # (save space)
        open_app(PLAYSTORE_PACKAGE_NAME, self.__transport_id, self.__device.info.arc_version)
        self.__driver.orientation = 'PORTRAIT'

    def __check_crash(self, package_name: str) -> bool:
        ''' Updates report if crash is detected.

            Args:
                - package_name: Name of the package to check.

            Returns:
                - True if a crash was detected.
        '''
        CrashType, crashed_act, msg = self.__err_detector.check_crash()
        if(not CrashType == CrashTypes.SUCCESS):
            self.__report.add_logs(package_name, self.__err_detector.logs)
            self.__report.add_history(package_name, f"{CrashType.value}: {crashed_act} - {msg}", self.__driver)
            self.__report.update_status(package_name, ValidationReport.FAIL, CrashType.value)
            return True
        return False

    def __scrape_dev_test_image(self):
        try:
            self.__driver.get_screenshot_as_file(
            f"/home/killuh/ws_p38/appium/src/notebooks/yolo_images/scraped_images/{self.dev_ss_count}.png"
            )
            self.dev_ss_count += 1
        except Exception as error:
            self.__dprint("Error w/ dev ss: ", error)


    def __dev_SS_loop(self):
        ''' Loop that pauses on input allowing to take multiple screenshots
                after manually changing app state.
        '''
        ans = ''
        while not (ans == 'q'):
            ans = input("Take your screen shots bro...")
            self.__dprint(f"{ans=}, {(not ans == 'q')}")
            if not (ans == 'q'):
                self.__dprint("Taking SS")
                self.__scrape_dev_test_image()
            else:
                self.__dprint("Quit from SS")



    def __process_app(self, app_title:str, app_package_name: str):
        self.__report.add_app(app_package_name, app_title)
        self.__err_detector.update_package_name(app_package_name)

        # Install
        installer = AppInstaller(self.__driver, self.__device, self.__instance_num)
        install_result: AppInstallerResult = installer.discover_and_install(app_title, app_package_name)
        self.__report.add_history(app_package_name, install_result.message or "App install successfull.", self.__driver)
        if install_result.price:
            self.__price_queue.put((app_title, app_package_name, install_result.price,))
            return self.__report.update_status(app_package_name, ValidationReport.FAIL, f"{install_result.message} - {install_result.price}")

        if self.__check_crash(app_package_name):
            return

        # Lauch App
        launcher = AppLauncher(self.__device, self.__app_list_queue, self.__instance_num)
        app_did_open, new_app_name, invalid_app, reason  = launcher.check_open_app(app_title, app_package_name)
        if new_app_name:
            self.__report.add_history(app_package_name, reason, self.__driver)
            return self.__process_app(new_app_name, app_package_name)
        elif invalid_app or not app_did_open:
            self.__report.add_history(app_package_name, reason, self.__driver)
            return self.__report.update_status(app_package_name, ValidationReport.FAIL, reason)

        if self.__check_crash(app_package_name):
            return

        # Now app is installed and launched...
        # info = AppInfo(self.__transport_id, app_package_name, self.__instance_num).info()
        # self.__report.update_app_info(app_package_name, info)

        self.__dev_SS_loop()

        # login_module = AppLogin(self.__driver, self.__device, self.__instance_num)
        # logged_in = login_module.login(app_title, app_package_name, info)

        # if self.__check_crash(app_package_name):
        #     return

        # self.__report.add_history(app_package_name,
        #     "Logged in." if logged_in else "Not logged in.", self.__driver)
        self.__report.update_status(app_package_name, ValidationReport.PASS, f"{logged_in=}")

    ##  Main Loop
    def run(self):
        '''
            Main loop of the Playstore class, starts the cycle of discovering,
            installing, logging in and uninstalling each app from self.__package_names.

            It ensures that the playstore is open at the beginning and that
            the device orientation is returned to portrait.
        '''

        self.__driver.orientation = 'PORTRAIT'
        for app_title, app_package_name in self.__package_names:
            # Allows for recursive call to retest an app.
            self.__process_app(app_title, app_package_name)
            self.__cleanup_run(app_package_name)

if __name__ == "__main__":
    pass