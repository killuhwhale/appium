import __main__
import collections
import os
import re
import requests
import subprocess
from datetime import datetime
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from bs4 import BeautifulSoup
from selenium.common.exceptions import (StaleElementReferenceException, NoSuchElementException,
                                        WebDriverException, ScreenshotException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from time import sleep, time
from typing import List


from objdetector.objdetector import ObjDetector
from utils.utils import (
    SIGN_IN, ArcVersions, CONTINUE, CrashType, GOOGLE_AUTH, IMAGE_LABELS, LOGIN,
    PASSWORD, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, ADB_KEYCODE_ENTER,
    check_crash, close_app, get_cur_activty, get_start_time, open_app)

class ValidationReport:
    '''
        A simple class to format the status report of AppValidator.
    '''
    PASS = 0
    FAIL = 1
    RED = "\033[31m"
    Black = "\033[30m"
    Green = "\033[32m"
    Yellow = "\033[33m"
    Blue = "\033[34m"
    Purple = "\033[35m"
    Cyan = "\033[36m"
    White = "\033[37m"
    RESET = "\033[0m"

    COLORS = [
        Black,
        White,
        RED,
        Green,
        Yellow,
        Blue,
        Purple,
        Cyan,
    ]

    REPEAT_TIMES = 2*len(COLORS)

    @staticmethod
    def empty_dict():
        '''
            Default value for a report key.
        '''
        return {"empty": 1}

    def __init__(self, report_title: str):
        self.report = collections.defaultdict(ValidationReport.empty_dict)
        self.report_title = report_title

    def add(self, package_name: str, app_name: str, status: int, reason: str):
        ''' Add report of a pacage if a report DNExist'''
        if "empty" in self.report[package_name]:
            self.report[package_name] = self.status_obj(status, reason, app_name)

    def status_obj(self, status: int, reason: str, name: str):
        ''' Status object containing the result information for each key/
            package in the report.
        '''
        return {
            'status': status,
            'reason': reason,
            'name': name,
            'report_title': self.report_title,
        }

    @staticmethod
    def ascii_footer():
        ''' Report decoration.'''
        print(ValidationReport.Green)

        print('''
               _  _     _  _     _  _     _   ___ _ _       _       _    _ _           _  _____     _  _     _  _     _  _
             _| || |_ _| || |_ _| || |_  | | / (_) | |     | |     | |  | | |         | ||____ |  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |/ / _| | |_   _| |__   | |  | | |__   __ _| |    / / |_  __  _|_  __  _|_  __  _|
             _| || |_ _| || |_ _| || |_  |    \| | | | | | | '_ \  | |/\| | '_ \ / _` | |    \ \  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |\  \ | | | |_| | | | | \  /\  / | | | (_| | |.___/ / |_  __  _|_  __  _|_  __  _|
              |_||_|   |_||_|   |_||_|   \_| \_/_|_|_|\__,_|_| |_|  \/  \/|_| |_|\__,_|_|\____/    |_||_|   |_||_|   |_||_|
        ''')
        print(ValidationReport.RESET)

    @staticmethod
    def ascii_header():
        ''' Report decoration.'''
        print(ValidationReport.Green)
        print('''
              _  _     _  _     _  _    ______                      _       _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  | ___ \                    | |    _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |_/ /___ _ __   ___  _ __| |_  |_  __  _|_  __  _|_  __  _|
            _| || |_ _| || |_ _| || |_  |    // _ \ '_ \ / _ \| '__| __|  _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |\ \  __/ |_) | (_) | |  | |_  |_  __  _|_  __  _|_  __  _|
             |_||_|   |_||_|   |_||_|   \_| \_\___| .__/ \___/|_|   \__|   |_||_|   |_||_|   |_||_|
                                                | |
                                                |_|
        ''')
        print(ValidationReport.RESET)

    @staticmethod
    def anim_starting():
        ''' Report decoration.'''
        print("\033[2J")  # clear the screen
        for i in range(ValidationReport.REPEAT_TIMES):
            color = ValidationReport.COLORS[i % 3]
            print("\033[0;0H")  # move cursor to top-left corner
            ValidationReport.ascii_starting(color)
            sleep(0.075)

    @staticmethod
    def ascii_starting(color=None):
        ''' Report decoration.'''
        if color is None:
            color = ValidationReport.Green
        print(color)
        print('''
              _  _     _  _     _  _     _____ _             _   _                         _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  /  ___| |           | | (_)                      _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| \ `--.| |_ __ _ _ __| |_ _ _ __   __ _          |_  __  _|_  __  _|_  __  _|
           _| || |_ _| || |_ _| || |_   `--. \ __/ _` | '__| __| | '_ \ / _` |          _| || |_ _| || |_ _| || |_
          |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |  | |_| | | | | (_| |  _ _ _  |_  __  _|_  __  _|_  __  _|
            |_||_|   |_||_|   |_||_|   \____/ \__\__,_|_|   \__|_|_| |_|\__, | (_|_|_)   |_||_|   |_||_|   |_||_|
                                                                         __/ |
                                                                        |___/
        ''')
        print(ValidationReport.RESET)

    def print_report(self):
        ''' Prints 'self' report.'''
        ValidationReport.print_reports(self.report)

    @staticmethod
    def sorted_name(p: List):
        ''' Serializable method to use for sorting. '''
        return p[0]

    @staticmethod
    def print_reports(report: collections.defaultdict):
        '''  Prints a given report. '''
        # Sorted by packge name
        ValidationReport.ascii_header()
        for package_name, status_obj in sorted(report.items(), key=ValidationReport.sorted_name):
            is_good = status_obj['status'] == ValidationReport.PASS
            print(ValidationReport.Blue, end="")
            print(f"{status_obj['name']} ", end="")
            print(ValidationReport.RESET, end="")
            print(f"{package_name} search/install status: ", end="")
            if is_good:
                print(ValidationReport.Green, end="")
                print("PASSED", end="")
                print(ValidationReport.RESET, end="")
                print(ValidationReport.Purple, end="")
                print(f" - [{status_obj['report_title']}]", end="")
                print(ValidationReport.RESET, end="")
                if len(status_obj['reason']) > 0:
                    print("\n\t\t", status_obj['reason'])
                print(ValidationReport.RESET, end="")

            else:
                print(ValidationReport.RED, end="")
                print("FAILED", end="")

                print(ValidationReport.RESET, end="")
                print(ValidationReport.Purple, end="")
                print(f" - [{status_obj['report_title']}]", end="")
                print(ValidationReport.RESET, end="")

                print("\n\t\t", status_obj['reason'])
                print(ValidationReport.RESET, end="")
            print()
        ValidationReport.ascii_footer()


class AppValidator:
    '''
        Main class to validate a broken app. Discovers, installs, opens and
        logs in to apps.
    '''

    PICUTRES = "/home/killuh/Pictures"
    def __init__(
            self,
            driver: webdriver.Remote,
            package_names: List[List[str]],
            transport_id: str,
            arc_version: ArcVersions,
            ip: str,
            instance_num: int= 0
        ):
        self.driver = driver
        self.package_names = package_names  # List of packages to test as [app_title, app_package_name]
        self.report = ValidationReport(ip)
        self.steps = [
            'Click search icon',
            'Send keys for search',
            'Click app icon',
            'Click install button',
        ]
        self.prev_act = None
        self.cur_act = None
        self.test_img = f"{ip}_test.png"
        self.detector = ObjDetector(self.test_img)
        self.transport_id = transport_id
        self.arc_version = arc_version
        self.ID = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}-{ip.split(':')[0]}"

    def dprint(self, text: str):
        color = self.report.COLORS[self.instance_num % len(self.report.COLORS)]
        print(color,end="")
        print(text,end="")
        print(color,end="")
        print(self.report.RESET)


    def check_playstore_invalid(self, package_name) -> bool:
        ''' Checks if an app's package_name is invalid vai Google playstore URL
            If invalid, returns True
            If valid, returns False
        '''

        url = f'https://play.google.com/store/apps/details?id={package_name}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            self.dprint(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            error_section = soup.find('div', {'id': 'error-section'})
            if error_section:
                return True
            else:
                return False
        else:
            return True


    def is_new_activity(self) -> bool:
        '''
            Calls adb shell dumpsys activity | grep mFocusedWindow
        '''
        package, activity = get_cur_activty(self.transport_id,  self.arc_version)
        act_name = f"{package}/{activity}"
        self.prev_act = self.cur_act  # Update
        self.cur_act = act_name
        # Init
        if self.prev_act is None:
            self.prev_act = act_name
        return self.prev_act != self.cur_act

    def get_test_ss(self) -> bool:
        '''
            Attempts to get SS of device and saves to a location where the
                object detector is configured to look.
            This image will be used as the source to detect our buttons and
                fields.
        '''

        # Removes first empty index and 'main.py' from "/path/to/src/main.py"
        #    ['', 'path', 'to', 'src', 'main.py']
        root_path = os.path.realpath(__main__.__file__).split("/")[1:-1]
        root_path = '/'.join(root_path)
        self.dprint("\n\n Saving SS to : ", f"/{root_path}/notebooks/yolo_images/test.png","\n\n")
        try:
            self.driver.get_screenshot_as_file(f"/{root_path}/notebooks/yolo_images/{self.test_img}")
            return True
        except ScreenshotException as e:
            self.dprint("App is scured!")
        except Exception as e:
            self.dprint("Error taking SS: ", e)

        self.dprint("Error taking SS: ", root_path)
        return False

    def get_error_ss(self, err_name: str) -> bool:
        '''
            Attempts to get SS of device when an error occures and saves to
                a given location.



        '''

        # Removes first empty index and 'main.py' from "/path/to/src/main.py"
        #    ['', 'path', 'to', 'src', 'main.py']
        root_path = os.path.realpath(__main__.__file__).split("/")[1:-1]
        root_path = '/'.join(root_path)
        path = f"/{root_path}/images/errors/{self.ID}"
        #Create dir
        if not os.path.exists(path):
            os.makedirs(path)

        self.dprint("\n\n Saving SS to : ", path,"\n\n")

        try:
            self.driver.get_screenshot_as_file(f"{path}/{err_name}.png")
            return True
        except ScreenshotException as e:
            self.dprint("App is scured!")
        except Exception as e:
            self.dprint("Error taking SS: ", e)

        self.dprint("Error taking SS: ", root_path)
        return False

    def sorted_conf(self, p: List):
        ''' Returns confidence value from the list.'''
        return int(p[2])

    def click_button(self, btns: List) -> List:
        '''
            Given a button list [Result from detector], remove the button and Click it

            Returns the remaining buttons.
        '''
        btns = sorted(btns, key=self.sorted_conf)
        self.dprint("Btns: ",btns )
        tapped = False
        if(len(btns) >= 1):
            btn = btns.pop()
            self.tap_screen(*self.get_coords(btn))
            tapped = True
        return btns, tapped


    def handle_login(self) -> bool:
        '''
            On a given page we will look at it and perform an action, if there is one .
        '''
        # Do
        self.is_new_activity() ## Init current activty
        self.get_test_ss()
        results = self.detector.detect()
        if results is None:
            return False

        # While

        # here we have a dict of results from detection
        # Consists of 4 labels
        # We want to prioritize
            # 1. Click Google Auth
            # 2. Filling out Email and Password
            # 3. Click Continue button to attempt to get to a page with #1 or #2
        actions = 0 # At most, we should take 3 actions on a single page [may not be necessary but is a hard limit to prevent loops.]
        # Find Email, Password and Login button.
        LOGIN_ENTERED = False
        PASSWORD_ENTERED = False
        CONTINUE_SUBMITTED = False
        tapped = False
        while actions < 8 and not CONTINUE_SUBMITTED:
            # input("Start handle login loop....")
            self.dprint("\n\n Activity \n", self.prev_act, "\n", self.cur_act )
            # input("Pause")
            if self.is_new_activity() or tapped:
                self.get_test_ss()
                self.dprint("\n\n New Activity \n", self.prev_act, "\n", self.cur_act )
                self.dprint("We found a new activity, take new screenshot and run detect again. ")
                results = self.detector.detect()
                tapped = False

            self.dprint("results: ", results)
            if GOOGLE_AUTH in results:
                # We have A google Auth button presents lets press it
                results[GOOGLE_AUTH], tapped = self.click_button(results[GOOGLE_AUTH])
                del results[GOOGLE_AUTH]
                return True
            elif LOGIN in results and not LOGIN_ENTERED:
                results[LOGIN], tapped = self.click_button(results[LOGIN])
                del results[LOGIN]
                self.send_keys_ADB("testminnie001@gmail.com", False)
                actions += 1
                LOGIN_ENTERED = True

            elif PASSWORD in results and not PASSWORD_ENTERED:
                results[PASSWORD], tapped = self.click_button(results[PASSWORD])
                del results[PASSWORD]
                self.send_keys_ADB("testminnie123")
                actions += 1
                PASSWORD_ENTERED = True
            elif CONTINUE in results:
                # TODO Remove the button once we click it, so we dont keep clicking the same element.
                results[CONTINUE], tapped = self.click_button(results[CONTINUE])
                del results[CONTINUE]
                actions += 1
                if LOGIN_ENTERED and PASSWORD_ENTERED:
                    CONTINUE_SUBMITTED = True
            elif SIGN_IN in results:
                results[SIGN_IN], tapped = self.click_button(results[SIGN_IN])
                del results[SIGN_IN]
                actions += 1
                if LOGIN_ENTERED and PASSWORD_ENTERED:
                    CONTINUE_SUBMITTED = True
            else:
                # No Keys in results
                return False


    def get_coords(self, btn: List):
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
        return str(int(x)), str(int(y))

    def run(self):
        '''
            Main loop of the Playstore class, starts the cycle of discovering,
            installing, logging in and uninstalling each app from self.package_names.

            It ensures that the playstore is open at the beginning and that
            the device orientation is returned to portrait.
        '''
        self.driver.orientation = 'PORTRAIT'
        for app_title, app_package_name in self.package_names:
            start_time = get_start_time()
            ERR = False
            installed, error = self.discover_and_install(app_title, app_package_name)
            # installed, error = True, False # Successful
            self.dprint(f"Installed? {installed}   err: {error}")
            if not installed and not error is None:
                self.report.add(app_package_name, app_title, ValidationReport.FAIL, error)
                ERR = True
                continue

            if not open_app(app_package_name, self.transport_id, self.arc_version):
                ERR = True
                if self.check_playstore_invalid(app_package_name):
                    self.report.add(app_package_name, app_title,
                        ValidationReport.FAIL,
                        "App package is invalid, update/ remove from list.")
                elif not self.is_installed(app_package_name):
                    self.report.add(app_package_name, app_title,
                        ValidationReport.FAIL,
                        "Failed to open because the package was not installed.")
                else:
                    self.report.add(app_package_name, app_title,
                        ValidationReport.FAIL,
                        "Failed to open")

            # TODO wait for activity to start intelligently, not just package
            # DEV: Using to scrape the first image of each app. (Will remove)
            if not ERR:
                # At this point we have successfully launched the app.
                # We can check
                sleep(5) # ANR Period
                CrashType, crashed_act = check_crash(app_package_name,
                                            start_time, self.transport_id)
                if(not CrashType == CrashType.SUCCESS):
                    self.report.add(app_package_name, app_title,
                        ValidationReport.FAIL, CrashType.value)
                    continue

                ###### Image Scraping #####
                # sleep(8)  # Wait for app to finsh loading the "MainActivity"
                _app_title = app_title.replace(" ", "_")  # Used to save screenshots of apps during DEV
                # DEV SS
                # self.driver.get_screenshot_as_file(
                #   f"/home/killuh/ws_p38/appium/src/notebooks/yolo_images/test.png"
                # )
                ###### END  Image Scraping #####

                # For now, if app opens without error, we'll report successful
                self.report.add(app_package_name, app_title,
                    ValidationReport.PASS, '')

                # TODO Do login, building obj detection
                login_attemps = 0
                logged_in = False
                while not logged_in and login_attemps < 4:
                    # ChromeOS does have mFocusedWindow -> get_cur_activty -> is_new_activity
                    # Throws an error and stays in continuous loop....
                    sleep(5)
                    logged_in = self.handle_login()
                    sleep(2) # Wait 2s, reattempt
                    login_attemps += 1
                if not logged_in:
                    self.report.add(app_package_name, app_title,
                        ValidationReport.PASS, 'Failed to log in')

                # input("Close app")
                close_app(app_package_name, self.transport_id)

                # Change the orientation to portrait
                self.driver.orientation = 'PORTRAIT'
                open_app(PLAYSTORE_PACKAGE_NAME, self.transport_id, self.arc_version)

                self.uninstall_app(app_package_name)  # (save space)

    def tap_screen(self, x:str, y:str):
        try:
            self.dprint(f"Tapping ({x},{y})")
            cmd = ('adb','-t', self.transport_id, 'shell', 'input', 'tap', x, y)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()
        except Exception as e:
            self.dprint("Error tapping app", e)
            return False
        return True

    def is_open(self, package_name: str) -> bool:
        cmd = ('adb', '-t', self.transport_id, 'shell', 'pidof', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        self.dprint(outstr)
        return len(outstr) > 0

    def is_installed(self, package_name: str) -> bool:
        """Returns whether package_name is installed.
        Args:
            package_name: A string representing the name of the application to
                be targeted.
        Returns:
            A boolean representing if package is installed.
        """
        cmd = ('adb', '-t', self.transport_id, 'shell', 'pm', 'list', 'packages')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
            capture_output=True).stdout.strip()
        full_pkg_regexp = fr'^package:({re.escape(package_name)})$'
        regexp = full_pkg_regexp

        # IGNORECASE is needed because some package names use uppercase letters.
        matches = re.findall(regexp, outstr, re.MULTILINE | re.IGNORECASE)
        if len(matches) == 0:
            self.dprint(f'No installed package matches "{package_name}"')
            return False
        if len(matches) > 1:
            self.dprint(f'More than one package matches "{package_name}":')
            for p in matches:
                self.dprint(f' - {p}')
            return False
        self.dprint(f'Found package name: "{matches[0]}"')
        return True

    def is_installed_UI(self):
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
                self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
                # # Pixel 2
                self.dprint("Searching for uninstall button....")
                self.dprint("Setting Ready to TRUE")
                ready = True
                break
            except Exception as e:
                self.dprint("App not ready to open, retrying...")
                sleep(0.5)

            try:
                self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Uninstall")
                ready = True
            except Exception as e:
                self.dprint("App not ready to open, retrying...")
                sleep(0.5)
        return ready

    def needs_purchase(self) -> bool:
        # Pixel 2
        # Chromebook (I think this works with Pixel2 also)
        try:
            content_desc = f'''
                new UiSelector().className("android.widget.Button").textMatches(\"\$\d+\.\d+\")
            '''
            self.dprint("Searching for Button with Price...", content_desc)
            self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            pass
        try:
            content_desc = f'''new UiSelector().descriptionMatches(\"\$\d+\.\d+\");'''
            self.dprint("Searching for Button with Price...", content_desc)
            self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            return False

    def needs_update(self) -> bool:
        '''
            Checks if apps needs an update via the UI on the playstore app details page.
        '''
        try:
            # Pixel 2
            # self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Update")
            content_desc = f'''new UiSelector().className("android.widget.Button").text("Update")'''
            self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            return True
        except Exception as e:
            return False

    def uninstall_multiple(self):
        for name in [pack_info[1] for pack_info in self.package_names]:
            self.uninstall_app(name)

    def uninstall_app(self, package_name: str):
        '''
            Uninstalls app and waits 40 seconds or so while checking if app is still installed.
            Returns True once app is fianlly unisntalled.
            Returns False if it takes too long to unisntall or some other unexpected error.
        '''
        uninstalled = False
        try:
            cmd = ( 'adb', '-t', self.transport_id, 'uninstall', package_name)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
            sleep(5)
            uninstalled = True
        except Exception as e:
            self.dprint("Error uninstalling: ", package_name, e)

        if uninstalled:
            try:
                sleep_cycle = 0
                while self.is_installed(package_name) and sleep_cycle <= 20:
                    sleep(2)
                    self.dprint("Sleeping.... zzz")
                    sleep_cycle += 1
                self.dprint(f"Took roughly {5 + sleep_cycle * 2} seconds.")
            except Exception as e:
                self.dprint("Error checking is installed after uninstall: ", package_name, e)

    def escape_chars(self, title: str):
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

    def return_error(self, last_step: int, error: str):
        if last_step == 0:
            self.driver.back()
            return [False, f"Failed: {self.steps[0]}"]
        elif last_step == 1:
            self.driver.back()
            return [False, f"Failed: {self.steps[1]}"]
        elif last_step == 2:
            self.driver.back()
            return [False, f"Failed: {self.steps[2]}"]
        elif last_step == 3:
            self.driver.back()
            self.driver.back()
            self.dprint(f"Failed: {self.steps[3]} :: {error}")
            return [False, f"Failed: {self.steps[3]} :: {error}"]

    def click_playstore_search(self):
        ''' Clicks Search Icon

            There is an animation when first opening app and the label is visible at first.
            This is a possible race conditoon between the driver.implicit_wait && the time it takes for the text to appear.

         '''
        self.dprint("Clicking search icon...")
        search_icon = None
        content_desc = f'''
            new UiSelector().className("android.widget.TextView").text("Search for apps & games")
        '''
        search_icon = self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        search_icon.click()

    def send_keys_ADB(self, title: str, submit=True):
        content_desc = f'''
            new UiSelector().className("android.widget.EditText")
        '''
        search_edit_text = self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        # search_edit_text.send_keys('\u270C  😸 ')
        search_edit_text.send_keys(title)
        # Old send text, unable to send unicode
        # cmd = ( 'adb', '-t', self.transport_id, 'shell', 'input', 'text', title_search)
        # subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        if submit:
            cmd = ( 'adb', '-t', self.transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        sleep(2)  # Wait for search results

    def press_app_icon(self, title: str):
        '''
            # Sometime the app has a different view on the same device.
            contentdesc = App: My Boy! - GBA Emulator Fast Emulator Arcade Star rating: 4.6 1,000,000+ downloads $4.99

            Emulator:
                Image of app or game icon for Roblox
        '''
        title_first = title.split(" ")[0]
        descs = [
            f'''new UiSelector().descriptionMatches(\".*{title_first}.*\");''', # Pixel 2
            f'''new UiSelector().descriptionMatches(\"App: {title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',  # Chromebooks
            f'''new UiSelector().descriptionMatches(\"{title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',
        ]
        app_icon = None
        for content_desc in descs:
            self.dprint("Searhing for app_icon with content desc: ", content_desc)
            try:
                app_icon = self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
                for icon in app_icon:
                    self.dprint("Icons:", icon.location, icon.id, icon.get_attribute("content-desc"))
                    if "Image" in icon.get_attribute('content-desc') or \
                        title_first in icon.get_attribute("content-desc"):
                        self.dprint("Clicked: ", icon.id, icon.get_attribute("content-desc"))
                        # input("Clicking app icon...")

                        icon.click()
                        sleep(2)
                        return

                    # input("Next icon...")
            except Exception as e:
                pass
        raise("Icon not found!")

    def extract_numbers(self, bounds: str):
        '''
            Given [882,801][1014,933], return [882,801,1014,933].
        '''
        return [int(x) for x in re.findall(r'\d+', bounds)]

    def click_unknown_install_btn(self, bounds: List[int]):
        self.dprint("Bounds", type(bounds), bounds)
        x1, y1, x2, y2 = bounds
        x = int(x2 * 0.75)
        y = (y1 + y2) // 2
        self.dprint("Tapping ",x ,y)
        self.tap_screen(str(x), str(y))
        sleep(2)

    def install_app_UI(self, install_package_name: str):
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
            content_desc = f'''
                new UiSelector().className("android.widget.Button").text("Install")
            '''
            install_BTN = self.driver.find_element(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value=content_desc)
            install_BTN.click()
        except Exception as e:  # Install btn not found
            err = True
            self.dprint("Failed to find 1st install button on transport id: ", self.transport_id)
            already_installed = self.is_installed(install_package_name)

        # Error finding/Clicking Install button  amd app is not installed still...
        if err and not already_installed:
            self.dprint("Verifying UI for Needs to Purchase...")
            if self.needs_purchase():
                self.dprint("raising needs purchase")
                raise Exception("Needs purchase")

            if self.needs_update():
                self.dprint("raising needs update")
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
            try:
                content_desc = f'''
                    new UiSelector().className("android.widget.Button").descriptionMatches("Install on more devices")
                '''
                install_BTN = self.driver.find_element(
                    by=AppiumBy.ANDROID_UIAUTOMATOR,
                    value=content_desc)
                bounds = self.extract_numbers(
                    install_BTN.get_attribute("bounds"))
                self.click_unknown_install_btn(bounds)
            except:
                raise Exception(
                    f"Program installed incorrect package,\
                        {install_package_name} was not actually installed")

        # We have successfully clicked an install buttin
        # 1. We wait for it to download. We will catch if its the correct package or not after installation.
        if not self.is_installed_UI():  # Waits up to 7mins to find install button.
            raise Exception("Failed to install app!!")

    def discover_and_install(self, title: str, install_package_name: str):
        '''
         A method to search Google Playstore for an app and install via the Playstore UI.
        '''
        try:
            error = None
            last_step = 0  # track last sucessful step to, atleast, report in console.


            # input("Press search icon # 1")
            self.click_playstore_search()
            # input("Press search icon # 1")

            last_step = 1
            self.send_keys_ADB(title)

            # input("Press app icon # 2")
            last_step = 2
            self.press_app_icon(title)
            # input("Press app icon # 2")

            last_step = 3

            # input("Step 3, press install")
            self.install_app_UI(install_package_name)
            # input("Step 3, press install")

            self.driver.back()  # back to seach results
            self.driver.back()  # back to home page
        except Exception as e:
            error = e
        finally:
            if error is None:
                return [True, None]
            else:

                self.get_error_ss(f"{title}_{self.steps[last_step].replace(' ','_')}")
                # Debug
                self.dprint("\n\n",
                    title,
                    install_package_name,
                    "Failed on step: ",
                    last_step,
                    self.steps[last_step])
                self.dprint("Eror:::: ", error)
                return self.return_error(last_step, error)



if __name__ == "__main__":
    pass