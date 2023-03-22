import collections
from multiprocessing import Queue
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime
from time import sleep, time
from typing import Dict, List, Any

import __main__
import requests
from appium.webdriver.common.appiumby import AppiumBy
from bs4 import BeautifulSoup
from selenium.common.exceptions import (ScreenshotException,)
from appium import webdriver
from objdetector.objdetector import ObjDetector
from utils.utils import (ACCOUNTS, ADB_KEYCODE_ENTER, CONFIG,
                         CONTINUE,  FACEBOOK_APP_NAME,
                         FACEBOOK_PACKAGE_NAME, GOOGLE_AUTH,
                         LOGIN, PASSWORD,
                         PLAYSTORE_PACKAGE_NAME, WEIGHTS, AppData, AppInfo, AppLogger,
                         BuildChannels, CrashTypes, Device,
                         ErrorDetector, close_app,
                         create_dir_if_not_exists, get_cur_activty,
                         get_root_path, is_download_in_progress, logger,
                         open_app, p_alert, p_blue, p_cyan, p_green, p_purple, p_red, p_yellow, save_resized_image,
                         transform_coord_from_resized)


class ANRThrownException(Exception):
    pass

class ValidationReport:
    '''
        A simple class to format the status report of AppValidator.
         = {
            report_title: {
                package_name: {
                    'status': -1,
                    'new_name': "",
                    'invalid:': False,
                    'reason': "",
                    'name': "",
                    'report_title': "",
                    'history': [],
                    'logs', '',
                },
                ...,
            },
            report_title2: {
                package_name: {
                    'status': -1,
                    'new_name': "",
                    'invalid:': False,
                    'reason': "",
                    'name': "",
                    'report_title': "",
                    'history': [],
                    'logs', '',
                },
                ...,
            }
        }
    '''
    PASS = 0
    FAIL = 1

    @staticmethod
    def default_dict():
        '''
            Default value for a report key.
        '''
        return  {
            'status': -1,
            'new_name': "",
            'invalid': False,
            'reason': "",
            'name': "",
            'package_name': "",
            'report_title': "",
            'history': [],
            'app_info': {}
        }

    def __init__(self, device: Device):
        # Device and Session information for the report.
        self.__device = device.info()
        self.__report_title = f'{self.__device.device_name}_{self.__device.ip}'
        self.__report = {self.__report_title: collections.defaultdict(ValidationReport.default_dict)}

    @property
    def report_title(self):
        return self.__report_title

    @property
    def report(self):
        return self.__report

    def add_app(self, package_name: str, app_name: str):
        ''' Adds an app to the report. '''
        if self.__report[self.__report_title][package_name]['status'] == -1:
            self.__report[self.__report_title][package_name]['package_name'] = package_name
            self.__report[self.__report_title][package_name]['name'] = app_name
            self.__report[self.__report_title][package_name]['report_title'] = self.__report_title
            self.__report[self.__report_title][package_name]['status'] = 0

    def update_app_info(self, package_name: str, info: AppData):
        self.__report[self.__report_title][package_name]['app_info'] = info

    def update_status(self, package_name: str, status: int, reason: str, new_name='', invalid=False):
        self.__report[self.__report_title][package_name]['status'] = status
        self.__report[self.__report_title][package_name]['reason'] = reason
        self.__report[self.__report_title][package_name]['new_name'] = new_name
        self.__report[self.__report_title][package_name]['invalid'] = invalid

    def add_history(self,package_name: str, history_msg: str, img_path: str=""):
        self.__report[self.__report_title][package_name]['history'].append({'msg':history_msg, 'img': img_path })

    def add_logs(self, package_name: str, logs: str):
        self.__report[self.__report_title][package_name]['logs'] = logs

    def get_status_obj_by_app(self, package_name: str):
        return self.__report[self.__report_title][package_name]

    def merge(self, oreport: 'ValidationReport'):
        ''' Merges on report title, used to merge pre-process Facebook login report. '''
        title_to_merge_on = self.__report_title
        self.__report[title_to_merge_on].update(deepcopy(oreport.report[title_to_merge_on]))

    @staticmethod
    def ascii_starting(color=None):
        ''' Report decoration.'''

        p_green('''
              _  _     _  _     _  _     _____ _            _   _                         _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  /  ___| |          | | (_)                      _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| \ `--.| |___ _ _ __| |_ _ _ __   __ _          |_  __  _|_  __  _|_  __  _|
           _| || |_ _| || |_ _| || |_   `--. \ __/ _` | '__| __| | '_ \ / _` |          _| || |_ _| || |_ _| || |_
          |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |  | |_| | | | | (_| |  _ _ _  |_  __  _|_  __  _|_  __  _|
            |_||_|   |_||_|   |_||_|   \____/ \__\__,_|_|   \__|_|_| |_|\__, | (_|_|_)   |_||_|   |_||_|   |_||_|
                                                                         __/ |
                                                                        |___/
        ''')

    @staticmethod
    def anim_starting():
        ''' Report decoration.'''
        print("\033[2J")  # clear the screen
        print("\033[0;0H")  # move cursor to top-left corner
        ValidationReport.ascii_starting()

    @staticmethod
    def ascii_header():
        ''' Report decoration.'''

        p_green('''
              _  _     _  _     _  _    ______                      _       _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  | ___ \                    | |    _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |_/ /___ _ __   ___  _ __| |_  |_  __  _|_  __  _|_  __  _|
            _| || |_ _| || |_ _| || |_  |    // _ \ '_ \ / _ \| '__| __|  _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |\ \  __/ |_) | (_) | |  | |_  |_  __  _|_  __  _|_  __  _|
             |_||_|   |_||_|   |_||_|   \_| \_\___| .__/ \___/|_|   \__|   |_||_|   |_||_|   |_||_|
                                                | |
                                                |_|
        ''')

    @staticmethod
    def ascii_footer():
        ''' Report decoration.'''
        p_green('''
               _  _     _  _     _  _     _   ___ _ _       _       _    _ _           _  _____     _  _     _  _     _  _
             _| || |_ _| || |_ _| || |_  | | / (_) | |     | |     | |  | | |         | ||____ |  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |/ / _| | |_   _| |__   | |  | | |__   __ _| |    / / |_  __  _|_  __  _|_  __  _|
             _| || |_ _| || |_ _| || |_  |    \| | | | | | | '_ \  | |/\| | '_ \ / _` | |    \ \  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |\  \ | | | |_| | | | | \  /\  / | | | (_| | |.___/ / |_  __  _|_  __  _|_  __  _|
              |_||_|   |_||_|   |_||_|   \_| \_/_|_|_|\__,_|_| |_|  \/  \/|_| |_|\__,_|_|\____/    |_||_|   |_||_|   |_||_|
        ''')

    @staticmethod
    def sorted_package_name(p: List):
        ''' Serializable method to use for sorting. Sorts by package_name '''
        return p[0]

    @staticmethod
    def sorted_app_name(p: List):
        ''' Serializable method to use for sorting. Sorts by app_name '''
        return p[1]['name']

    @staticmethod
    def sorted_device_name(p: List):
        ''' Serializable method to use for sorting. '''
        return p['report_title']

    @staticmethod
    def print_app_report(package_name: str, status_obj: Dict):
        if status_obj['status'] == -1:
            return
        is_good = status_obj['status'] == ValidationReport.PASS
        p_blue(f"{status_obj['name']} ", end="")
        p_cyan(f"{package_name} ", end="")
        if is_good:
            p_green("PASSED", end="")
        else:
            p_red(f"FAILED", end="")
            p_red(f"New  name: {status_obj['new_name']}", end="") if status_obj['new_name'] else print('', end='')
            p_red(f"Playstore N/A", end="") if status_obj['invalid'] else print('', end='')
        p_purple(f" - [{status_obj['report_title']}]", end="\n")

        p_blue(status_obj['app_info'], end='\n')

        if len(status_obj['reason']) > 0:
            logger.print_log("\t", "Final status: ", end="")
            p_green( status_obj['reason']) if is_good else p_red( status_obj['reason'])

        # Print History
        for hist in status_obj['history']:
            p_yellow("\t", hist['msg'])
            p_yellow("\t\t", f"Img: {hist['img']}")
        logger.print_log()

    @staticmethod
    def print_report(report: 'ValidationReport'):
        '''  Prints all apps from a single report. '''
        # Sorted by packge name
        ValidationReport.ascii_header()
        for package_name, status_obj in sorted(report.report[report.report_title].items(), key=ValidationReport.sorted_package_name):
            ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()

    def print(self):
        ''' Prints 'self' report.'''
        ValidationReport.print_report(self)

    def print_reports(reports: List['ValidationReport']):
        ''' Prints app reports from a list of ValidationReport.
            This results in each device's report being print one after the other.
            So apps will not be grouped together.
        '''
        ValidationReport.ascii_header()
        for report in reports:
            for package_name, status_obj in sorted(report.report[report.report_title].items(), key=ValidationReport.sorted_package_name):
                ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()

    @staticmethod
    def group_reports_by_app(reports: List['ValidationReport']) -> collections.defaultdict(list):
        all_reports = collections.defaultdict(list)
        for report_instance in reports:
            for package_name, status_obj in report_instance.report[report_instance.report_title].items():
                all_reports[package_name].append(status_obj)
                all_reports[package_name] = sorted(all_reports[package_name], key=ValidationReport.sorted_device_name)
        return all_reports

    @staticmethod
    def print_reports_by_app(reports: List['ValidationReport']):
        ''' Reorders the reports so that all apps are printed grouped together.

            Makes for better view in summary report, we can compare each app's final status.
        '''
        all_reports = ValidationReport.group_reports_by_app(reports)

        ValidationReport.ascii_header()
        for package_name, status_objs in sorted(all_reports.items(), key=ValidationReport.sorted_package_name):
            for status_obj in status_objs:
                ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()


class AppValidator:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.
    '''
    def __init__(
            self,
            driver: webdriver.Remote,
            package_names: List[List[str]],
            device: Device,
            instance_num: int,
            app_list_queue: Queue,
            app_logger: AppLogger,
            stats_queue: Queue,
        ):
        self.__app_list_queue = app_list_queue
        self.__stats_queue = stats_queue
        self.__app_logger = app_logger
        self.__driver = driver
        self.__device = device.info()
        self.__ip = self.__device.ip
        self.__transport_id = self.__device.transport_id
        self.__arc_version = self.__device.arc_version
        self.__is_emu = self.__device.is_emu
        self.__package_names = package_names  # List of packages to test as [app_title, app_package_name]
        self.__current_package = None
        self.__err_detector = ErrorDetector(self.__transport_id, self.__arc_version)
        self.__report = ValidationReport(device)

        self.__steps = [
            'Click search icon',
            'Send keys for search',
            'Click app icon',
            'Click install button',
        ]
        self.__prev_act = None
        self.__cur_act = None
        # Path for SS location for detector.
        self.__test_img_fp = f"{self.__ip}_test.png"
        self.__weights = WEIGHTS
        self.__detector = ObjDetector(self.__test_img_fp, [self.__weights])
        self.__name_span_text = ''
        self.__misnamed_reason_text = "App name does not match the current name on the playstore."
        self.__instance_num = instance_num if instance_num else 0
        self.dev_ss_count = 320
        # self.ID = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}-{self.__ip.split(':')[0]}"

    @property
    def report(self):
        return self.__report

    def __dprint(self, *args):
        if not CONFIG.debug_print:
            return

        n = self.__instance_num % 6  # 6 colors to pick from
        if(n == 0):
            p_red(f"{self.__ip} - ", *args)
        elif(n == 1):
            p_green(f"{self.__ip} - ", *args)
        elif(n == 2):
            p_yellow(f"{self.__ip} - ", *args)
        elif(n == 3):
            p_blue(f"{self.__ip} - ", *args)
        elif(n == 4):
            p_purple(f"{self.__ip} - ", *args)
        elif(n == 5):
            p_cyan(f"{self.__ip} - ", *args)


    def __is_new_activity(self) -> bool:
        '''
            Calls adb shell dumpsys activity | grep mFocusedWindow

            Raises
        '''
        results: Dict = get_cur_activty(self.__transport_id,  self.__arc_version, self.__current_package)
        if results['is_ANR_thrown']:
            raise ANRThrownException(results)


        act_name = f"{results['package_name']}/{results['act_name']}"
        self.__prev_act = self.__cur_act  # Update
        self.__cur_act = act_name
        # Init
        if self.__prev_act is None:
            self.__prev_act = act_name
        return self.__prev_act != self.__cur_act

    def __is_installed(self, package_name: str) -> bool:
        """Returns whether package_name is installed.
        Args:
            package_name: A string representing the name of the application to
                be targeted.
        Returns:
            A boolean representing if package is installed.
        """
        cmd = ('adb', '-t', self.__transport_id, 'shell', 'pm', 'list', 'packages')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
            capture_output=True).stdout.strip()
        full_pkg_regexp = fr'^package:({re.escape(package_name)})$'
        regexp = full_pkg_regexp

        # IGNORECASE is needed because some package names use uppercase letters.
        matches = re.findall(regexp, outstr, re.MULTILINE | re.IGNORECASE)
        if len(matches) == 0:
            self.__dprint(f'No installed package matches "{package_name}"')
            return False
        if len(matches) > 1:
            self.__dprint(f'More than one package matches "{package_name}":')
            for p in matches:
                self.__dprint(f' - {p}')
            return False
        self.__dprint(f'Found package name: "{matches[0]}"')
        return True

    def __uninstall_app(self, package_name: str, force_rm: bool= False):
        '''
            Uninstalls app and waits 40 seconds or so while checking if app is still installed.
            Returns True once app is fianlly unisntalled.
            Returns False if it takes too long to unisntall or some other unexpected error.
        '''
        if  package_name in [PLAYSTORE_PACKAGE_NAME] and not force_rm:
            print(f"Not uninstalling {package_name}")
            return False

        uninstalled = False
        try:
            print("Uninstalling ", package_name)
            cmd = ( 'adb', '-t', self.__transport_id, 'uninstall', package_name)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
            sleep(1)
            uninstalled = True
        except Exception as e:
            self.__dprint("Error uninstalling: ", package_name, e)

        if uninstalled:
            try:
                sleep_cycle = 0
                while self.__is_installed(package_name) and sleep_cycle <= 20:
                    sleep(2)
                    self.__dprint("Sleeping.... zzz")
                    sleep_cycle += 1
                self.__dprint(f"Took roughly {5 + sleep_cycle * 2} seconds.")
            except Exception as e:
                self.__dprint("Error checking is installed after uninstall: ", package_name, e)

    def uninstall_multiple(self):
        for app_info in self.__package_names:
            package_name = app_info[1]
            self.__uninstall_app(package_name)


    ##  Http Get
    def __check_playstore_invalid(self, package_name) -> bool:
        ''' Checks if an app's package_name is invalid via Google playstore URL
            If invalid, returns True
            If valid, returns False
        '''

        url = f'https://play.google.com/store/apps/details?id={package_name}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # self.__dprint(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            error_section = soup.find('div', {'id': 'error-section'})
            if error_section and error_section.text == "We're sorry, the requested URL was not found on this server.":
                return True
            else:
                return False
        else:
            return True

    def __check_playstore_name(self, package_name, app_title) -> str:
        ''' Checks an app's name via Google playstore URL

            Returns:
                - the apps name from the playstore.
        '''

        url = f'https://play.google.com/store/apps/details?id={package_name}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # self.__dprint(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')

            error_section = soup.find('div', {'id': 'error-section'})
            if error_section and error_section.text == "We're sorry, the requested URL was not found on this server.":
                return app_title

            name_span_parent = soup.find('h1', {'itemprop': 'name'})
            name_span = name_span_parent.findChild('span')
            print(f"{name_span.text=}")
            if name_span:
                self.__name_span_text = name_span.text
                return name_span.text
            else:
                return app_title
        else:
            return app_title  # returning app title essentially means there was no change found.


    ##  Buttons
    def __sorted_conf(self, p: List):
        ''' Returns confidence value from the list.'''
        return int(p[2])

    def __tap_screen(self, x:str, y:str):
        try:
            self.__dprint(f"Tapping ({x},{y})")
            cmd = ('adb','-t', self.__transport_id, 'shell', 'input', 'tap', x, y)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()
        except Exception as e:
            self.__dprint("Error tapping app", e)
            return False
        return True

    def __get_coords(self, btn: List):
        ''' Given a list of list representing a bounding box's top left &
            bottom right corners, return the mid point as a string to be
            compatible with adb shell input text.

            Args:
                btn = [[x1, y1], [x2, y2]]
            Returns:
                (x, y): List[str]
         '''
        x = (btn[0][0] + btn[1][0]) / 2
        y = (btn[0][1] + btn[1][1]) / 2

        # coords = transform_coord_from_resized(
        #     (self.__device['wxh']),
        #     (1200, 800),
        #     (int(x), int(y))
        # )
        # return str(int(coords[0])), str(int(coords[1]))
        return str(int(x)), str(int(y))

    def __click_button(self, btns: List) -> List:
        '''
            Given a button list [Result from ObjDetector], remove the button and click it.

            Returns the remaining buttons.
        '''
        btns = sorted(btns, key=self.__sorted_conf)  # Sorted by confidence
        self.__dprint("Btns: ",btns )
        tapped = False
        if(len(btns) >= 1):
            btn = btns.pop()
            self.__tap_screen(*self.__get_coords(btn))
            tapped = True
        return btns, tapped


    ##  Images/ Reporting
    def __get_test_ss(self) -> bool:
        '''
            Attempts to get SS of device and saves to a location where the
                object detector is configured to look.
            This image will be used as the source to detect our buttons and
                fields.
        '''

        # Removes first empty index and 'main.py' from "/path/to/src/main.py"
        #    ['', 'path', 'to', 'src', 'main.py']
        # root_path = os.path.realpath(__main__.__file__).split("/")[1:-1]
        # root_path = '/'.join(root_path)
        root_path = get_root_path()
        try:
            self.__driver.get_screenshot_as_file(f"{root_path}/notebooks/yolo_images/{self.__test_img_fp}")
            # png_bytes = self.__driver.get_screenshot_as_png()
            # save_resized_image(png_bytes, (1200,800), f"/{root_path}/notebooks/yolo_images/{self.__test_img_fp}")

            return True
        except ScreenshotException as e:
            self.__dprint("App is scured!")
        except Exception as e:
            self.__dprint("Error taking SS: ", e)

        self.__dprint("Error taking SS: ", root_path)
        return False

    def __scrape_dev_test_image(self):
        try:
            self.__driver.get_screenshot_as_file(
            f"/home/killuh/ws_p38/appium/src/notebooks/yolo_images/scraped_images/{self.dev_ss_count}.png"
            )
            self.dev_ss_count += 1
        except Exception as error:
            print("Error w/ dev ss: ", error)

    def __dev_SS_loop(self):
        ''' Loop that pauses on input allowing to take multiple screenshots
                after manually changing app state.
        '''
        ans = ''
        while not (ans == 'q'):
            ans = input("Take your screen shots bro...")
            print(f"{ans=}, {(not ans == 'q')}")
            if not (ans == 'q'):
                print("Taking SS")
                self.__scrape_dev_test_image()
            else:
                print("Quit from SS")


    ##  Reporting
    def __update_report_history(self, package_name: str, msg: str):
        '''
            Updates Validation report for the given package_name.

            This will add a history message and take a screenshot to document
            the testing process of an app.

            Args:
                msg: A message to commit to history.
        '''
        try:
            num = len(self.__report.report[self.__report.report_title][package_name]['history'])
            path = f"{get_root_path()}/images/history/{self.__ip}/{package_name}"
            create_dir_if_not_exists(path)
            full_path = f"{path}/{num}.png"
            self.__driver.get_screenshot_as_file(full_path)
            self.__report.add_history(package_name, msg, full_path)
        except Exception as error:
            print("Failed to get SS", error)
            self.__report.add_history(package_name, msg)

    def __return_error(self, last_step: int, error: str):
        if last_step == 0:
            self.__driver.back()
            return [False, f"Failed: {self.__steps[0]}"]
        elif last_step == 1:
            self.__driver.back()
            return [False, f"Failed: {self.__steps[1]}"]
        elif last_step == 2:
            self.__driver.back()
            return [False, f"Failed: {self.__steps[2]}"]
        elif last_step == 3:
            self.__driver.back()
            self.__driver.back()
            self.__dprint(f"Failed: {self.__steps[3]} :: {error}")
            return [False, f"Failed: {self.__steps[3]} :: {error}"]


    ##  Typing
    def __escape_chars(self, title: str):
        title_search = title.replace("'", "\\'")
        title_search = title_search.replace(" ", "\ ")
        title_search = title_search.replace('"', '\\"')
        title_search = title_search.replace("&", "\&")
        title_search = title_search.replace("-", "\-")
        title_search = title_search.replace("!", "\!")
        title_search = title_search.replace("?", "\?")
        title_search = title_search.replace("@", "\@")
        title_search = title_search.replace("#", "\#")
        title_search = title_search.replace("$", "\$")
        title_search = title_search.replace("%", "\%")
        title_search = title_search.replace("+", "\+")
        return title_search

    def __send_keys_ADB(self, title: str, submit=True, esc=True):
        title_search = title
        if esc:
            title_search = self.__escape_chars(title)

        # for _ in range(len("testminnie001@gmail.com") + 5):
        #     cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_DEL)
        #     subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

        for c in title_search:
            cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'text', c)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        if submit:
            cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

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
        )

        '''
            Currently, I am collecting a list of reports and collect them.
            Instead, I should send the status object.
            Then I can just update a dict of reports istead of a list.
            The status obj has the report_title, and package_name
        '''
        self.__send_stats_update(status_obj)

        self.__prev_act = None
        self.__cur_act = None
        close_app(app_package_name, self.__transport_id)
        self.__uninstall_app(app_package_name)  # (save space)
        open_app(PLAYSTORE_PACKAGE_NAME, self.__transport_id, self.__arc_version)
        self.__driver.orientation = 'PORTRAIT'
        self.__name_span_text = ''  # reset misnamed app's new name

    def __check_crash(self, package_name: str) -> bool:
        CrashType, crashed_act, msg = self.__err_detector.check_crash()
        if(not CrashType == CrashTypes.SUCCESS):
            self.__report.add_logs(package_name, self.__err_detector.logs)
            self.__update_report_history(package_name, f"{CrashType.value}: {crashed_act} - {msg}")
            self.__report.update_status(package_name, ValidationReport.FAIL, CrashType.value)
            return True
        return False

    ## Logging in.
    def __sleep_while_in_progress(self, app_package_name: str):
        ''' Sleeps while in download is in progress.

            Used to wait for a game to download its extra content.
        '''
        timeout = 60 * 3
        start = time()
        while is_download_in_progress(self.__transport_id, app_package_name) and time() - start < timeout:
            print(f"DLinProgress...")
            sleep(1.5)

    def __handle_login(self, login_entered_init: bool, password_entered_init:bool, is_game: bool, app_package_name: str) -> bool:
        '''
            On a given page we will look at it and perform an action, if there is one .
        '''
        # Do
        empty_retries = 2
        self.__is_new_activity() ## Init current activty
        if not self.__get_test_ss():
            return False, login_entered_init, password_entered_init
        results = self.__detector.detect()
        login_entered, password_entered = login_entered_init, password_entered_init
        if results is None:
            return False, login_entered, password_entered

        # While

        # here we have a dict of results from detection
        # Consists of 4 labels
        # We want to prioritize
            # 1. Click Google Auth
            # 2. Filling out Email and Password
            # 3. Click Continue button to attempt to get to a page with #1 or #2
        # Find Email, Password and Login button.


        CONTINUE_SUBMITTED = False
        tapped = False
        detect_attempt = 0
        while not (CONTINUE_SUBMITTED and login_entered and password_entered) and detect_attempt < 3:
            if CONTINUE_SUBMITTED and login_entered and password_entered:
                return True, True, True


            if GOOGLE_AUTH in results:
                # We have A google Auth button presents lets press it
                results[GOOGLE_AUTH], tapped = self.__click_button(results[GOOGLE_AUTH])
                del results[GOOGLE_AUTH]
                return True, login_entered, password_entered
            elif LOGIN in results and not login_entered:
                print("Click login        <-------")
                results[LOGIN], tapped = self.__click_button(results[LOGIN])
                del results[LOGIN]
                if app_package_name in ACCOUNTS:
                    login_val = ACCOUNTS[app_package_name][0]
                    self.__send_keys_ADB(login_val, False, False)
                    print(f"Send Login - {login_val}        <-------")
                else:
                    print(f"Login info not created for {app_package_name}")

                login_entered = True

            elif PASSWORD in results and not password_entered:
                print("Click Password        <-------")
                results[PASSWORD], tapped = self.__click_button(results[PASSWORD])
                del results[PASSWORD]
                if app_package_name in ACCOUNTS:
                    pass_val = ACCOUNTS[app_package_name][1]
                    self.__send_keys_ADB(pass_val, False, False)
                    print(f"Send Password - {pass_val}       <-------")
                    password_entered = True
                else:
                    print(f"Password info not created for {app_package_name}")
                sleep(3)
                if self.__is_new_activity():
                    return True, login_entered, password_entered
            elif CONTINUE in results:
                # TODO Remove the button once we click it, so we dont keep clicking the same element.
                print("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                del results[CONTINUE]

                print("App is game: ", is_game)
                if is_game:
                    sleep(0.600)
                    self.__sleep_while_in_progress(app_package_name)

                print(f"Cont w/ login and password entered {login_entered=} {password_entered=}")
                if login_entered and password_entered:
                    sleep(5)  # Wait for a possible login to happen
                    return True, login_entered, password_entered

            if self.__is_new_activity():
                if not self.__get_test_ss():
                    return False, login_entered, password_entered
                self.__dprint("\n\n New Activity \n", self.__prev_act, "\n", self.__cur_act, '\n\n' )
                results = self.__detector.detect()
                if results is None:
                    return False, login_entered, password_entered
                tapped = False
                self.__dprint(f"Results: ", results)
            elif len(results.keys()) == 0 and empty_retries > 0:
                empty_retries -= 1
                print("Empty results, grabbing new SS and processing...")
                sleep(2)
                # Get a new SS, ir error return
                if not self.__get_test_ss():
                    return False, login_entered, password_entered
                results = self.__detector.detect()
            detect_attempt += 1
        return False, login_entered, password_entered

    def __attempt_login(self, app_title: str, app_package_name: str, is_game: bool):
        fb_login_continue_after_login = app_package_name == FACEBOOK_PACKAGE_NAME
        print(f"{fb_login_continue_after_login=}")

        login_attemps = 0
        logged_in = False
        login_entered = False
        password_entered = False
        while not logged_in and login_attemps < 4:
            if self.__check_crash(app_package_name):
                break

            try:
                res = self.__handle_login(login_entered,
                                        password_entered,
                                        is_game,
                                        app_package_name)
                logged_in, login_entered, password_entered = res
                print(f"\n\n After attempt login: ", login_attemps)
                print(f"{logged_in=}, {login_entered=}, {password_entered=} \n\n")

                if logged_in and not fb_login_continue_after_login:
                    break
                elif logged_in and fb_login_continue_after_login:
                    print("Logged in to FB! Reattempting for save info continue...")
                    res = self.__handle_login(login_entered,
                                        password_entered,
                                        is_game,
                                        app_package_name)
                    break
                login_attemps += 1

            except ANRThrownException as error_obj:
                p_alert(f"ANR thrown - {app_title} - {app_package_name}")
                if error_obj['ANR_for_package'] == app_package_name:
                    self.__update_report_history(app_package_name, "ANR thrown.")
                    self.__report.update_status(app_package_name, ValidationReport.FAIL, CrashTypes.ANR.value)
                    return False


        # Check for crash once more after login attempts.
        if self.__check_crash(app_package_name):
            return False

        if not logged_in:
            self.__report.update_status(app_package_name, ValidationReport.PASS, 'Not logged in.')
            self.__update_report_history(app_package_name, "Not logged in.")
            return False
        else:
            # For now, if app opens without error, we'll report successful
            self.__report.update_status(app_package_name, ValidationReport.PASS, 'Logged in.')
            self.__update_report_history(app_package_name, "Logged in.")
        return True


    ## PlayStore install discovery
    def __is_installed_UI(self):
        '''
            Checks for the presence of the Uninstall button indicating that the
                app has completely finished installing.

            Using adb shows that the app is installed well before PlayStore UI
                says its ready to open.
        '''
        max_wait = 420  # 7 mins, Large gaming apps may take a while to download.
        content_desc = 'Uninstall'
        ready = False
        t = time()
        while not ready and (time() - t) < max_wait:
            try:
                content_desc = f'''
                    new UiSelector().className("android.widget.Button").text("Uninstall")
                '''
                self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
                # # Pixel 2
                self.__dprint("Searching for uninstall button....")
                self.__dprint("Setting Ready to TRUE")
                ready = True
                break
            except Exception as e:
                self.__dprint("App not ready to open, retrying...")
                sleep(0.5)

            try:
                self.__driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Uninstall")
                ready = True
            except Exception as e:
                self.__dprint("App not ready to open, retrying...")
                if t > max_wait * 0.25:
                    self.__check_playstore_crash()
                sleep(0.5)
            self.__driver.orientation = 'PORTRAIT'
        return ready

    def __needs_purchase(self) -> bool:
        # Pixel 2
        # Chromebook (I think this works with Pixel2 also)
        try:
            content_desc = f'''
                new UiSelector().className("android.widget.Button").textMatches(\"\$\d+\.\d+\")
            '''
            self.__dprint("Searching for Button with Price...", content_desc)
            self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            pass
        try:
            content_desc = f'''new UiSelector().descriptionMatches(\"\$\d+\.\d+\");'''
            self.__dprint("Searching for Button with Price...", content_desc)
            self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            return False

    def __needs_update(self) -> bool:
        '''
            Checks if apps needs an update via the UI on the playstore app details page.
        '''
        try:
            # Pixel 2
            # self.__driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Update")
            content_desc = f'''new UiSelector().className("android.widget.Button").text("Update")'''
            self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            return False

    def __click_playstore_search(self):
        ''' Clicks Search Icon

            There is an animation when first opening app and the label is visible at first.
            This is a possible race conditoon between the driver.implicit_wait && the time it takes for the text to appear.

         '''
        self.__dprint("Clicking search icon...")
        search_icon = None
        content_desc = f'''
            new UiSelector().className("android.widget.TextView").text("Search for apps & games")
        '''
        search_icon = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        search_icon.click()

    def __check_playstore_crash(self):
        # 01-05 22:08:57.546   129   820 I WindowManager: WIN DEATH: Window{afca274 u0 com.android.vending/com.google.android.finsky.activities.MainActivity}
        cur_package = self.__err_detector.get_package_name()
        self.__err_detector.update_package_name(PLAYSTORE_PACKAGE_NAME)
        CrashType, crashed_act, msg = self.__err_detector.check_crash()
        self.__err_detector.update_package_name(cur_package)  # switch back to package
        if(not CrashType == CrashTypes.SUCCESS):
            # TODO() Determine what to do when this scenario happens.
            self.__dprint("PlayStore crashed ", CrashTypes.value)
            # self.__driver.reset()  # Reopen app
            raise Exception("PLAYSTORECRASH")

    def __search_playstore(self, title: str, submit=True):
        content_desc = f'''
            new UiSelector().className("android.widget.EditText")
        '''
        search_edit_text = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        # search_edit_text.send_keys('\u270C  😸 ')
        search_edit_text.send_keys(title)
        # Old send text, unable to send unicode
        # cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'text', title_search)
        # subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        if submit:
            cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        sleep(2)  # Wait for search results

    def __press_app_icon(self, title: str):
        '''
            # Sometime the app has a different view on the same device.
            contentdesc = App: My Boy! - GBA Emulator Fast Emulator Arcade Star rating: 4.6 1,000,000+ downloads $4.99

            Emulator:
                Image of app or game icon for Roblox
        '''
        title_first = title.split(" ")[0]
        descs = [
            f'''new UiSelector().descriptionMatches(\".*(?i){title_first}.*\");''', # Pixel 2
            f'''new UiSelector().descriptionMatches(\"App: (?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',  # Chromebooks
            f'''new UiSelector().descriptionMatches(\"(?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',
        ]
        app_icon = None
        for content_desc in descs:
            self.__dprint("Searhing for app_icon with content desc: ", content_desc)
            try:
                app_icon = self.__driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
                for icon in app_icon:
                    self.__dprint("Icons:", icon.location, icon.id, icon.get_attribute("content-desc"))
                    if "Image" in icon.get_attribute('content-desc') or \
                        title_first in icon.get_attribute("content-desc"):
                        self.__dprint("Clicked: ", icon.id, icon.get_attribute("content-desc"))
                        icon.click()
                        sleep(2)
                        return

            except Exception as e:
                pass
        raise Exception("Icon not found!")

    def __extract_bounds(self, bounds: str):
        '''
            Given '[882,801][1014,933]', return [882,801,1014,933].
        '''
        return [int(x) for x in re.findall(r'\d+', bounds)]

    def __click_unknown_install_btn(self, bounds: List[int]):
        self.__dprint("Bounds", type(bounds), bounds)
        x1, y1, x2, y2 = bounds
        x = int(x2 * 0.75)
        y = (y1 + y2) // 2
        self.__dprint("Tapping ",x ,y)
        self.__tap_screen(str(x), str(y))

    def __install_app_UI(self, install_package_name: str):
        '''
            We are on the app detail page:
            1. Install
            2. Price
            3. Cancel / Play[Open]
            4. Uninstall / Play[Open]

        '''
        already_installed = False  # Potentailly already isntalled
        err = False
        try:
            if self.__is_emu:
                content_desc = f'''
                    new UiSelector().className("android.widget.Button").descriptionMatches("Install on more devices")
                '''
                print(f"Looking at {content_desc=}")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ANDROID_UIAUTOMATOR,
                    value=content_desc)
                bounds = self.__extract_bounds(
                    install_BTN.get_attribute("bounds"))
                self.__click_unknown_install_btn(bounds)
            elif self.__device.channel == BuildChannels.STABLE:
                # ARC_P CoachZ -> find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Install")
                print(f"Looking at ACCESSIBILITY_ID, value=Install")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ACCESSIBILITY_ID, value="Install")
                install_BTN.click()
            else:
                # For some reason Helios acts weirdly and not the same as EVE which is also ARC-R...
                # i think if its not on stable channel this works....
                # ARC_R Helios -> driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value='''new UiSelector().className("android.widget.View").text("Install")''')
                content_desc = f'''
                    new UiSelector().className("android.widget.Button").text("Install")
                '''
                print(f"Looking at {content_desc=}")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ANDROID_UIAUTOMATOR,
                    value=content_desc)
                install_BTN.click()


        except Exception as e:  # Install btn not found
            err = True
            self.__dprint("Failed to find install button on transport id: ", self.__transport_id)
            already_installed = self.__is_installed(install_package_name)

        # Error finding/Clicking Install button  amd app is not installed still...
        if err and not already_installed:
            self.__dprint("Verifying UI for Needs to Purchase...")
            if self.__needs_purchase():
                self.__dprint("raising needs purchase")
                raise Exception("Needs purchase")

            if self.__needs_update():
                self.__dprint("raising needs update")
                raise Exception("Needs update")

            # Now, Install and Price, Update are not present,
            # To get here, we must be looking for a package
            # com.abc.foogame
            # When we search by name, foogame,
            # The app foogame, by com.zyx.foogames is actually showing.
            # So we check if the packge is installed via ADB cmd because this will be a source of truth
            # Therefore, at this point we have an installed app, that doesnt match our targeted package name.
            # TODO() :NOTE: On the first run, it will install this package and report as correct....

            # However, on emualtors, we can still check for the install button since it is not the same as other devices
            # If Install btn not found, PRice or Update not present, check for "Install on more devices" button, if found we are
            #   most liekly on an emulator and we can click install.
            print(f"Program may have installed an incorrect package, {install_package_name} was not actually installed")
            raise Exception(f"{install_package_name} was not installed.")
        # We have successfully clicked an install buttin
        # 1. We wait for it to download. We will catch if its the correct package or not after installation.
        if not self.__is_installed_UI():  # Waits up to 7mins to find install button.
            raise Exception("Failed to install app!!")

    def __discover_and_install(self, title: str, install_package_name: str):
        '''
         A method to search Google Playstore for an app and install via the Playstore UI.
        '''
        try:
            error = None
            last_step = 0  # track last sucessful step to, atleast, report in console.


            # input("Press search icon # 1")
            self.__click_playstore_search()
            # input("Press search icon # 1")
            self.__check_playstore_crash()

            last_step = 1
            self.__search_playstore(title)
            self.__check_playstore_crash()

            # input("Press app icon # 2")
            last_step = 2
            self.__press_app_icon(title)
            self.__check_playstore_crash()
            # input("Press app icon # 2")

            last_step = 3

            # input("Step 3, press install")
            self.__install_app_UI(install_package_name)
            self.__check_playstore_crash()
            # input("Step 3, press install")
            self.__update_report_history(install_package_name, "App discovery and installation process successful.")
            self.__driver.back()  # back to seach results
            self.__driver.back()  # back to home page
        except Exception as e:
            error = e
        finally:
            if error is None:
                return [True, None]
            elif error == "PLAYSTORECRASH":
                raise Exception(error)
            else:
                self.__update_report_history(install_package_name, f"Discovery/ install failure: {self.__steps[last_step]}")
                # Debug
                self.__dprint("\n\n",
                    title,
                    install_package_name,
                    "Failed on step: ",
                    last_step,
                    self.__steps[last_step])
                self.__dprint("Eror:::: ", error)
                return self.__return_error(last_step, error)

    def __handle_failed_open_app(self, package_name: str, app_title: str, msg: str) -> str:
        reason = ''
        NEW_APP_NAME = ''
        INVALID_APP = False
        if self.__check_playstore_invalid(package_name):
            reason = "Package is invalid and was removed from the list."
            INVALID_APP = True
            self.__app_list_queue.put(('invalid', package_name, app_title))
        elif not app_title == self.__check_playstore_name(package_name, app_title):
            reason = f"[{app_title} !=  {self.__name_span_text}] {self.__misnamed_reason_text}"
            NEW_APP_NAME = self.__name_span_text
            self.__app_list_queue.put(('misnamed', package_name, NEW_APP_NAME))

        elif not self.__is_installed(package_name):
            reason = f"Not installed - {msg}"
        else:
            reason = msg


        self.__report.update_status(package_name, ValidationReport.FAIL, reason, NEW_APP_NAME, INVALID_APP)
        self.__update_report_history(package_name, f"{reason}")
        return reason

    def __send_stats_update(self, status_obj: ValidationReport.default_dict):
        self.__stats_queue.put(status_obj)

    def __process_app(self, app_title: str, app_package_name: str):
        self.__current_package = app_package_name
        self.__report.add_app(app_package_name, app_title)
        self.__err_detector.reset_start_time()
        self.__err_detector.update_package_name(app_package_name)
        try:
            installed, error = self.__discover_and_install(app_title, app_package_name)
            self.__dprint(f"Installed? {installed}   err: {error}")

            if not installed and not error is None:
                reason = self.__handle_failed_open_app(app_package_name, app_title, f"[{app_title} {error}")
                if self.__misnamed_reason_text in reason:
                    # Retry app again
                    p_alert(f"{self.__ip} - ", "Retrying app with new name: ", self.__name_span_text)
                    return self.__process_app(self.__name_span_text, app_package_name)
                self.__cleanup_run(app_package_name)
                return

            if not open_app(app_package_name, self.__transport_id, self.__arc_version):
                reason = self.__handle_failed_open_app(app_package_name, app_title, "Failed to open")
                if self.__misnamed_reason_text in reason:
                    # Retry app again
                    p_alert(f"{self.__ip} - ", "Retrying app with new name: ", self.__name_span_text)
                    return self.__process_app(self.__name_span_text, app_package_name)

                self.__check_crash(app_package_name)
                self.__cleanup_run(app_package_name)
                return

            info = AppInfo(self.__transport_id, app_package_name).info()
            self.__report.update_app_info(app_package_name, info)
            print(f"App {info=}")
            sleep(5) # ANR Period
            if self.__check_crash(app_package_name):
                self.__cleanup_run(app_package_name)
                return

            self.__update_report_history(app_package_name, "App launch successful.")
            # self.__dev_SS_loop()

            if info and not info.is_pwa:
                logged_in = self.__attempt_login(app_title, app_package_name, info.is_game)
                print(f"Attempt loging: {logged_in=}")

        except Exception as error:
            p_alert(f"{self.__ip} - ", f"Error in main RUN: {app_title} - {app_package_name}", error)
            if error == "PLAYSTORECRASH":
                self.__dprint("restart this attemp!")


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

class FacebookApp:
    ''' Specific instance of AppValidator to install and login to facebook for
        further auth.

        This will be ran before the main valdiation process.
    '''
    def __init__(self, driver: webdriver.Remote, app_logger: AppLogger,  device: Device, instance_num: int, stats_queue: Queue):
        self.__app_name = FACEBOOK_APP_NAME
        self.__package_name = FACEBOOK_PACKAGE_NAME
        self.__device = device
        self.__validator = AppValidator(
            driver,
            [[self.__app_name, self.__package_name],],
            device,
            instance_num,
            Queue(),
            app_logger,
            stats_queue,

        )

    @property
    def validator(self):
        return self.__validator

    def install_and_login(self):
        ''' Runs app valdiator to install, launch and login to Facebook.
        '''
        if not CONFIG.login_facebook:
            p_alert(f"Skipping pre-process FB install {CONFIG.login_facebook=}")
            return
        self.__validator.uninstall_app(self.__package_name, force_rm=True)
        self.__validator.run()
        sleep(3)
        close_app(self.__package_name, self.__device.info().transport_id)

if __name__ == "__main__":
    pass