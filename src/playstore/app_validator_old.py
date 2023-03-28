from multiprocessing import Queue
import re
import subprocess
from time import sleep, time
from typing import Dict, List
import __main__
import requests
from appium.webdriver.common.appiumby import AppiumBy
from bs4 import BeautifulSoup
from selenium.common.exceptions import (ScreenshotException,)
from appium import webdriver
from objdetector.objdetector import ObjDetector
from playstore.validation_report import ValidationReport
from utils.app_utils import AppInfo, close_app, create_dir_if_not_exists, get_cur_activty, get_root_path, is_download_in_progress, open_app
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import AppLogger, p_alert, p_blue, p_cyan, p_green, p_purple, p_red, p_yellow
from utils.utils import (ACCOUNTS, ADB_KEYCODE_ENTER, CONFIG,
                         CONTINUE,  FACEBOOK_APP_NAME,
                         FACEBOOK_PACKAGE_NAME, FB_ATUH, GOOGLE_AUTH,
                         LOGIN, PASSWORD, PLAYSTORE_PACKAGE_NAME, WEIGHTS)


class ANRThrownException(Exception):
    pass

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
        self.__device = device.info
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
        self.dev_ss_count = 8
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
            self.__dprint(f"Not uninstalling {package_name}")
            return False

        uninstalled = False
        try:
            self.__dprint("Uninstalling ", package_name)
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
            self.__dprint(f"{name_span.text=}")
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
            sleep(1.5)  # Allows for things to load before taking SS.
            self.__driver.get_screenshot_as_file(full_path)
            self.__report.add_history(package_name, msg, full_path)
        except Exception as error:
            self.__dprint("Failed to get SS", error)
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
            status_obj['logs'],
        )

        self.__send_stats_update(status_obj)

        self.__prev_act = None
        self.__cur_act = None
        close_app(app_package_name, self.__transport_id)
        self.__uninstall_app(app_package_name)  # (save space)
        open_app(PLAYSTORE_PACKAGE_NAME, self.__transport_id, self.__arc_version)
        self.__driver.orientation = 'PORTRAIT'
        self.__name_span_text = ''  # reset misnamed app's new name

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
            self.__dprint(f"DLinProgress...")
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
                return True, True, True
            elif FB_ATUH in results and not login_entered:
                results[FB_ATUH], tapped = self.__click_button(results[FB_ATUH])
                del results[FB_ATUH]
                return True, True, True # Conisdered email and password entered
            elif LOGIN in results and not login_entered:
                self.__dprint(f"Click login        <------- {login_entered=}")
                results[LOGIN], tapped = self.__click_button(results[LOGIN])
                del results[LOGIN]
                if app_package_name in ACCOUNTS:
                    login_val = ACCOUNTS[app_package_name][0]
                    self.__send_keys_ADB(login_val, False, False)
                    self.__dprint(f"Send Login - {login_val}        <-------")
                else:
                    self.__dprint(f"Login info not created for {app_package_name}")
                login_entered = True


            elif PASSWORD in results and not password_entered:
                self.__dprint("Click Password        <-------")
                results[PASSWORD], tapped = self.__click_button(results[PASSWORD])
                del results[PASSWORD]
                if app_package_name in ACCOUNTS:
                    pass_val = ACCOUNTS[app_package_name][1]
                    self.__send_keys_ADB(pass_val, False, False)
                    self.__dprint(f"Send Password - {pass_val}       <-------")
                    password_entered = True
                else:
                    self.__dprint(f"Password info not created for {app_package_name}")
                if self.__is_new_activity():
                    return True, login_entered, password_entered
            elif CONTINUE in results:
                # TODO Remove the button once we click it, so we dont keep clicking the same element.
                self.__dprint("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                del results[CONTINUE]

                self.__dprint("App is game: ", is_game)
                if is_game:
                    sleep(0.600)
                    self.__sleep_while_in_progress(app_package_name)

                self.__dprint(f"Cont w/ login and password entered {login_entered=} {password_entered=}")
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
                self.__dprint("Empty results, grabbing new SS and processing...")
                # sleep(2)
                # Get a new SS, ir error return
                if not self.__get_test_ss():
                    return False, login_entered, password_entered
                results = self.__detector.detect()
            detect_attempt += 1
        return False, login_entered, password_entered

    def __attempt_login(self, app_title: str, app_package_name: str, is_game: bool):
        # We need to press the submit buttton on the screen following the login
        # in order to use Facebook as an auth app for other apps like games.
        fb_login_continue_after_login = app_package_name == FACEBOOK_PACKAGE_NAME
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
                self.__dprint(f"\n\n After attempt login: ", login_attemps)
                self.__dprint(f"{logged_in=}, {login_entered=}, {password_entered=} \n\n")

                if logged_in and not fb_login_continue_after_login:
                    break
                elif logged_in and fb_login_continue_after_login:
                    self.dprint("Logged in to FB! Reattempting for save info continue...")
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
                # TODO() rethink this part.
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

    def __click_app_icon(self, title: str):
        '''
            # Sometime the app has a different view on the same device.
            contentdesc = App: My Boy! - GBA Emulator Fast Emulator Arcade Star rating: 4.6 1,000,000+ downloads $4.99

            Emulator:
                Image of app or game icon for Roblox
        '''

        # TODO() Confirm this change is okay to make. Retest apps....
        # title_first = title.split(" ")[0]
        title_first = title
        descs = [
            f'''new UiSelector().descriptionMatches(\".*(?i){title_first}.*\");''', # Pixel 2
            f'''new UiSelector().descriptionMatches(\"App: (?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',  # Chromebooks
            f'''new UiSelector().descriptionMatches(\"(?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \\n]*\");''',
        ]
        app_icon = None
        clicked = False
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
                        sleep(2)  # Too small of a break and the click doesnt seem to work.
                        return

            except Exception as e:
                self.__dprint("Icon failed click ", e)

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
                self.__dprint(f"Looking at {content_desc=}")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ANDROID_UIAUTOMATOR,
                    value=content_desc)
                bounds = self.__extract_bounds(
                    install_BTN.get_attribute("bounds"))
                # If Install btn not found, PRice or Update not present, check for "Install on more devices" button, if found we are
                #   most liekly on an emulator and we can click install.
                self.__click_unknown_install_btn(bounds)


            # Cant find a rhyme or reason as to why ACCESSIBILITY_ID
            # Is sometimes present and other time it is not.
            # E.g. Flash stable eve to non-dev and back to dev. Now its gone.
            try:
                self.__dprint(f"Looking at ACCESSIBILITY_ID, value=Install")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ACCESSIBILITY_ID, value="Install")
                install_BTN.click()
                return
            except Exception as error:
                self.__dprint("First install method failed.")

            content_desc = f'''
                new UiSelector().className("android.widget.Button").text("Install")
            '''
            self.__dprint(f"Looking at {content_desc=}")
            install_BTN = self.__driver.find_element(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value=content_desc)
            install_BTN.click()

        except Exception as e:  # Install btn not found
            err = True
            self.__dprint("Failed to find install button on transport id: ", self.__transport_id, error)
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
            self.__dprint(f"Program may have installed an incorrect package, {install_package_name} was not actually installed")
            raise Exception(f"{install_package_name} was not installed.")
        # We have successfully clicked an install buttin
        # We wait for it to download. We will catch if its the correct package or not after installation.
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
            self.__click_app_icon(title)
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
            self.__dprint(f"App {info=}")
            sleep(5) # ANR Period
            if self.__check_crash(app_package_name):
                self.__cleanup_run(app_package_name)
                return

            self.__update_report_history(app_package_name, "App launch successful.")
            # self.__dev_SS_loop()

            if info and not info.is_pwa:
                logged_in = self.__attempt_login(app_title, app_package_name, info.is_game)
                self.__dprint(f"Attempt loging: {logged_in=}")
                sleep(5)
                self.__check_crash(app_package_name)




        except Exception as error:
            p_alert(f"{self.__ip} - ", f"Error in main RUN: {app_title} - {app_package_name}", error)
            if error == "PLAYSTORECRASH":
                self.__dprint("Playstore crashed!")  # Havent encountered this in a long time.


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