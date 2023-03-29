import subprocess
from time import sleep, time
from typing import Dict, List
import __main__
from selenium.common.exceptions import (ScreenshotException,)
from appium import webdriver
from objdetector.objdetector import ObjDetector
from utils.app_utils import AppInfo, get_cur_activty, get_root_path, is_download_in_progress
from utils.device_utils import Device
from utils.error_utils import ErrorDetector
from utils.logging_utils import get_color_printer, p_alert
from utils.utils import (ACCOUNTS, ADB_KEYCODE_ENTER, CONTINUE,
                         FACEBOOK_PACKAGE_NAME, FB_ATUH, GOOGLE_AUTH, LOGIN,
                         PASSWORD, WEIGHTS)


class ANRThrownException(Exception):
    pass

class AppLogin:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.
    '''
    def __init__(
            self,
            driver: webdriver.Remote,
            device: Device,
            instance_num: int
        ):
        self.__driver = driver
        self.__current_package = None
        self.__device = device
        self.__err_detector = ErrorDetector(self.__device.info.transport_id, self.__device.info.arc_version)
        self.__prev_act = None
        self.__cur_act = None
        # Path for SS location for detector.
        self.__test_img_fp = f"{self.__device.info.ip}_test.png"
        self.__weights = WEIGHTS
        self.__detector = ObjDetector(self.__test_img_fp, [self.__weights])
        self.__dprint = get_color_printer(instance_num)

    def __is_new_activity(self) -> bool:
        ''' Calls adb shell dumpsys activity | grep mFocusedWindow/

            Raises ANRThrownException
        '''
        results: Dict = get_cur_activty(self.__device.info.transport_id,  self.__device.info.arc_version, self.__current_package)
        if results['is_ANR_thrown']:
            raise ANRThrownException(results)


        act_name = f"{results['package_name']}/{results['act_name']}"
        self.__prev_act = self.__cur_act  # Update
        self.__cur_act = act_name
        # Init
        if self.__prev_act is None:
            self.__prev_act = act_name
        return self.__prev_act != self.__cur_act

    ##  Buttons
    def __sorted_conf(self, p: List):
        ''' Returns confidence value from the list.'''
        return int(p[2])

    def __tap_screen(self, x:str, y:str):
        try:
            self.__dprint(f"Tapping ({x},{y})")
            cmd = ('adb','-t', self.__device.info.transport_id, 'shell', 'input', 'tap', x, y)
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
        #     cmd = ( 'adb', '-t', self.__device.info.transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_DEL)
        #     subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

        for c in title_search:
            cmd = ( 'adb', '-t', self.__device.info.transport_id, 'shell', 'input', 'text', c)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        if submit:
            cmd = ( 'adb', '-t', self.__device.info.transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

    ## Logging in.
    def __sleep_while_in_progress(self, app_package_name: str):
        ''' Sleeps while in download is in progress.

            Used to wait for a game to download its extra content.
        '''
        timeout = 60 * 3
        start = time()
        while is_download_in_progress(self.__device.info.transport_id, app_package_name) and time() - start < timeout:
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
            print(f"{results=}")
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
                sleep(3)
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
            # if self.__check_crash(app_package_name):
            #     break

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
        return logged_in

    ## PlayStore install discovery
    def login(self, app_title: str, app_package_name: str, app_info: AppInfo):
        ''' Attempts to log in to an app.
            TODO() implement behavior below.
            Args:
                - login_method: The method to use to login with.

            Returns:
                - dict containing the status of logged in and method used to log in.
        '''
        self.__current_package = app_package_name
        self.__err_detector.reset_start_time()
        self.__err_detector.update_package_name(app_package_name)
        try:
            sleep(3)
            return self.__attempt_login(app_title, app_package_name, app_info.is_game)

        except Exception as error:
            p_alert(f"{self.__device.info.ip} - ", f"Error in main RUN: {app_title} - {app_package_name}", error)
            if error == "PLAYSTORECRASH":
                self.__dprint("Playstore crashed!")  # Havent encountered this in a long time.
            return False


if __name__ == "__main__":
    pass