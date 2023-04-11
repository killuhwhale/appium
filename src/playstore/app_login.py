import __main__
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from PIL import Image
import subprocess
import traceback
from time import perf_counter, sleep, time
from typing import Dict, List
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (ScreenshotException,)
from appium import webdriver
from objdetector.objdetector import ObjDetector
from objdetector.yolov8 import YoloV8
from playstore.app_login_results import AppLoginResults
from playstore.validation_report import ValidationReport
from utils.accounts import ACCOUNTS
from utils.app_utils import AppInfo, clear_app, get_cur_activty, get_root_path, is_download_in_progress, open_app
from utils.device_utils import Device
from utils.logging_utils import get_color_printer, p_alert
from utils.secure_app_logins import SECURE_APPS
from utils.utils import (ADB_KEYCODE_ENTER, CONTINUE,
                         FACEBOOK_PACKAGE_NAME, FB_ATUH, GOOGLE_AUTH, LOGIN,
                         PASSWORD, V8_WEIGHTS, WEIGHTS, save_resized_image)


class ANRThrownException(Exception):
    pass


class AppLogin:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.

          After a few sample runs comparing v5 and v8, as well as getting SS as file vs in-mem PNG/ PIL Image, it seems
          Yolo Version:
            - v8 detections are better so far
            - cant find any exmples yet as to whether or not resizing an image improves accuracy.
          File types:
            - the speed isnt much different

    '''
    def __init__(
            self,
            driver: webdriver.Remote,
            device: Device,
            report: ValidationReport,
            dprinter
        ):
        self.__driver = driver
        self.__device = device
        self.__report = report

        self.__prev_act = None
        self.__cur_act = None

        # Detection
        self.__using_v8 = True
        img_name = f"{self.__device.info.ip}_test.png"
        self.__test_img_fp = f"{get_root_path()}/notebooks/yolo_images/{img_name}"  # req for v5 input
        self.__detector_v5 = ObjDetector(self.__test_img_fp, [WEIGHTS])  # v5
        self.__detector_v8 = YoloV8(weights=V8_WEIGHTS)
        # Debug printing
        self.__dprint = dprinter



    def __is_new_activity(self, app_package_name: str) -> bool:
        ''' Calls adb shell dumpsys activity | grep mFocusedWindow/

            Raises ANRThrownException
        '''
        results: Dict = get_cur_activty(self.__device.info.transport_id,  self.__device.info.arc_version, app_package_name)
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
        print("sorting by conf: list => ", p)
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

            results=defaultdict(<class 'list'>, {'Continue': [ (1015, 694), (1161, 743), 0.3802167475223541] })
            results=defaultdict(<class 'list'>, {'Continue': [ ((1018, 790), (1163, 840), tensor(0.52810, device='cuda:0') ), ((812, 779), (1364, 850), tensor(0.87382, device='cuda:0'))]
        '''
        self.__dprint("Btns: ",btns )
        btns = sorted(btns, key=self.__sorted_conf)  # Sorted by confidence
        self.__dprint("Sorted Btns: ",btns )
        tapped = False
        if(len(btns) >= 1):
            btn = btns[0]
            self.__tap_screen(*self.__get_coords(btn))
            tapped = True
        return btns, tapped

    ##  Images/ Reporting
    def __detect_v5(self) -> defaultdict(list):
        ''' Yolov5
            Attempts to get SS of device and saves to a location where the
                object detector is configured to look.
            This image will be used as the source to detect our buttons and
                fields.
        '''
        start = perf_counter()
        root_path = get_root_path()
        try:
            self.__driver.get_screenshot_as_file(self.__test_img_fp)
            # png_bytes = self.__driver.get_screenshot_as_png()
            # save_resized_image(png_bytes, (1200,800), f"/{root_path}/notebooks/yolo_images/{self.__test_img_fp}")
            end = perf_counter()
            print(f"\n\n Getting image and resizing took (v5): {(end - start):.6f} \n\n")
            return self.__detector_v5.detect()
        except ScreenshotException as e:
            self.__dprint("App is scured!")
        except Exception as e:
            self.__dprint("Error taking SS: ", e)

        self.__dprint("Error taking SS: ", root_path)
        return defaultdict(list)

    def __detect_v8(self) -> bool:
        '''
            Attempts to get SS of device as Pil Image and returns results for detection.
        '''
        try:
            start = perf_counter()
            png_bytes = self.__driver.get_screenshot_as_png()
            src = Image.open(BytesIO(png_bytes))
            # src.resize((640,640), resample=Image.NEAREST)
            # src.resize((640,640))  # BICUBIC by default
            # src.resize((640,640), resample=Image.LANCZOS)
            end = perf_counter()
            print(f"\n\n Getting image and resizing took: {(end - start):.6f}s \n\n")
            return self.__detector_v8.detect(src)
        except ScreenshotException as e:
            self.__dprint("App is scured!")
        except Exception as e:
            self.__dprint("Error taking SS: ", e)
        return defaultdict(list)

    def __detect(self) -> defaultdict(list):
        start = perf_counter()
        res = defaultdict(list)
        if self.__using_v8:
            res = self.__detect_v8()
        else:
            res = self.__detect_v5()
        end = perf_counter()
        self.__dprint(f"\n\n Entire detection process took ({self.__using_v8=}): {(end - start):.6f}s \n\n")
        return res

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

    def __clean_result(self, key: str, results: defaultdict):
        '''
            Removes detection from the list under a given key, removes entry when list is empty.
        '''
        num_detections = len(results[key])
        # print(f"Cleaning {key=} w/ {num_detections=}")
        # print(f"{results=}")
        if num_detections == 0:
            return
        elif num_detections > 1:
            del results[key][0]
        else:
            del results[key]
        # print(f"After {results=}")


    def __handle_google_login(self, is_game: bool, app_package_name: str):
        ''' Looks for Google Auth buttons and Continue buttons until reaching Google Auth button.

            Clicks on account within GAuth dialogs.

            Returns:
                - True when Gauth is found and email is successfully clicked.
        '''
        GOOGLE_SUBMITTED = False
        has_google = False
        empty_retries = 2
        attempts = 5

        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not GOOGLE_SUBMITTED and empty_retries >= 0 and attempts > 0:
            attempts -= 1
            # if self.__driver.current_activity == '.common.account.SimpleDialogAccountPickerActivity':
            #     if app_package_name in ACCOUNTS:
            #         login_val = ACCOUNTS[app_package_name][0]
            #         content_desc = f'''new UiSelector().text("{login_val}")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         content_desc = f'''new UiSelector().className("android.widget.Button").text("OK")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         return True
            # elif self.__driver.current_activity == '.games.ui.signinflow.SignInActivity':
            #     if app_package_name in ACCOUNTS:
            #         login_val = ACCOUNTS[app_package_name][0]
            #         self.__driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value='Expand account list.').click()
            #         content_desc = f'''new UiSelector().className("android.widget.TextView").text("{login_val}")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         self.__driver.find_element(by=AppiumBy.ID, value='continue_as_button').click()
            #         sleep(5)

            results: defaultdict = self.__detect()
            self.__dprint(f"Results: ", results)
            if not len(results.keys()):
                empty_retries -= 1
                sleep(5)
                self.__sleep_while_in_progress(app_package_name)

            elif GOOGLE_AUTH in results:
                results[GOOGLE_AUTH], tapped = self.__click_button(results[GOOGLE_AUTH])
                has_google = True
                del results[GOOGLE_AUTH]
                sleep(5)
                if self.__driver.current_activity == '.common.account.AccountPickerActivity' and app_package_name in ACCOUNTS:
                    login_val = ACCOUNTS[app_package_name][0]
                    content_desc = f'''new UiSelector().text("{login_val}")'''
                    self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
                    self.__report.add_history(app_package_name, "Google Auth sign-in", self.__driver)
                    GOOGLE_SUBMITTED = True
                    return True, has_google
                else:
                    p_alert(f"Found Google Auth login but not associated account for {app_package_name=}")

            elif CONTINUE in results:
                print("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                print("App is game: ", is_game)
                if is_game:
                    sleep(5)
                    self.__sleep_while_in_progress(app_package_name)

        return False, has_google

    def __handle_facebook_login(self, is_game: bool, app_package_name: str):
        ''' Looks for Facebook Auth buttons and Continue buttons until reaching Facebook Auth button.

            Clicks on account within FacebookAuth dialogs.

            Returns:
                - True when Facebook auth is found and email is successfully clicked.
        '''
        FACEBOOK_SUBMITTED = False
        has_facebook = False
        empty_retries = 2
        attempts = 4
        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not FACEBOOK_SUBMITTED and empty_retries >= 0 and attempts >=0:
            attempts -= 1
            # if self.__driver.current_activity == '.common.account.SimpleDialogAccountPickerActivity':
            #     if app_package_name in ACCOUNTS:
            #         login_val = ACCOUNTS[app_package_name][0]
            #         content_desc = f'''new UiSelector().text("{login_val}")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         content_desc = f'''new UiSelector().className("android.widget.Button").text("OK")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         return True

            # elif self.__driver.current_activity == '.games.ui.signinflow.SignInActivity':
            #     if app_package_name in ACCOUNTS:
            #         login_val = ACCOUNTS[app_package_name][0]
            #         self.__driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value='Expand account list.').click()
            #         content_desc = f'''new UiSelector().className("android.widget.TextView").text("{login_val}")'''
            #         self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
            #         self.__driver.find_element(by=AppiumBy.ID, value='continue_as_button').click()
            #         sleep(5)

            results: defaultdict = self.__detect()
            self.__dprint(f"Results: ", results)
            if not len(results.keys()):
                empty_retries -= 1
                sleep(5)
                self.__sleep_while_in_progress(app_package_name)

            elif FB_ATUH in results:
                results[FB_ATUH], tapped = self.__click_button(results[FB_ATUH])
                has_facebook = True
                sleep(5) # Wait for FB Dialog to Appear..
                if self.__driver.current_activity == '.gdp.ProxyAuthDialog':
                    content_desc = f'''new UiSelector().className("android.widget.Button").text("Continue")'''
                    self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()

                self.__report.add_history(app_package_name, "Facebook Auth sign-in", self.__driver)
                del results[GOOGLE_AUTH]
                return True, has_facebook


            elif CONTINUE in results:
                print("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                print("App is game: ", is_game)
                if is_game:
                    sleep(5)
                    self.__sleep_while_in_progress(app_package_name)
        return False, has_facebook

    def __attempt_click_continue(self):
        '''
            Attempts new detection and clicks a continue button.

            Used to click 'save' when loggin into Facebook app.
        '''
        results: defaultdict = self.__detect()
        if CONTINUE in results:
            results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
            return True
        return False

    def __handle_password_login(self, is_game: bool,
                              app_package_name: str):

        login_entered = password_entered = False
        CONTINUE_SUBMITTED = False
        has_email = False
        empty_retries = 3
        attemtps = 6 # When a detect occurs on a non-clickable element, we need to break from the loop

        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not (CONTINUE_SUBMITTED and login_entered and password_entered) and empty_retries > 0 and attemtps >= 0:
            attemtps -= 1
            if CONTINUE_SUBMITTED and login_entered and password_entered:
                return True, True, True

            results: defaultdict = self.__detect()
            self.__dprint(f"Results: ", results)
            if not len(results.keys()):
                empty_retries -= 1
                sleep(2)
                if empty_retries == 0:
                    return False

            elif LOGIN in results and not login_entered:
                print("Click login        <-------")
                results[LOGIN], tapped = self.__click_button(results[LOGIN])
                has_email = True
                del results[LOGIN]

                if app_package_name in ACCOUNTS:
                    login_val = ACCOUNTS[app_package_name][0]
                    self.__send_keys_ADB(login_val, False, False)
                    print(f"Send Login - {login_val}        <-------")

                else:
                    p_alert(f"Login info not created for {app_package_name} but found an email/password login")
                    return False, has_email
                login_entered = True

            elif PASSWORD in results and not password_entered:
                print("Click Password        <-------")
                results[PASSWORD], tapped = self.__click_button(results[PASSWORD])
                has_email = True
                del results[PASSWORD]
                if app_package_name in ACCOUNTS:
                    pass_val = ACCOUNTS[app_package_name][1]
                    self.__send_keys_ADB(f"{pass_val}\n", False, False)
                    print(f"Send Password - {pass_val}       <-------")
                    password_entered = True
                else:
                    p_alert(f"Password info not created for {app_package_name} but found an email/password login")
                    return False, has_email
                sleep(3)

            elif CONTINUE in results:
                print("Click Continue        <-------")
                # input("Click Continue...")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                print("App is game: ", is_game)
                if is_game:
                    sleep(5)
                    self.__sleep_while_in_progress(app_package_name)

                print(f"Cont w/ login and password entered {login_entered=} {password_entered=}")
                if login_entered and password_entered:
                    CONTINUE_SUBMITTED = True
                    if app_package_name == FACEBOOK_PACKAGE_NAME:
                        # Click one more contine button
                        sleep(5)  # Wait for a possible login to happen
                        fb_attempts = 3
                        while not self.__attempt_click_continue() and fb_attempts > 0:
                            fb_attempts -= 1
                            sleep(1)

                    sleep(5)  # Wait once more for app loading
                    self.__report.add_history(app_package_name, "Email/ password sign-in", self.__driver)
                    return True, has_email

        return False, has_email

    # Old
    def __handle_login(self, login_entered_init: bool, password_entered_init:bool, is_game: bool, app_package_name: str) -> bool:
        '''
            On a given page we will look at it and perform an action, if there is one .
        '''
        # Do
        empty_retries = 2
        self.__is_new_activity(app_package_name) ## Init current activty
        results: defaultdict = self.__detect()
        if not len(results.keys()):
            return False, login_entered_init, password_entered_init
        login_entered, password_entered = login_entered_init, password_entered_init

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
            self.__dprint("App is game: ", is_game)
            if is_game:
                sleep(0.600)
                self.__sleep_while_in_progress(app_package_name)

            self.__dprint(f"Current {results=}")




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
                if self.__is_new_activity(app_package_name):
                    return True, login_entered, password_entered
            elif CONTINUE in results:
                self.__dprint("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                self.__dprint(f"Cont w/ login and password entered {login_entered=} {password_entered=}")
                if login_entered and password_entered:
                    sleep(5)  # Wait for a possible login to happen
                    return True, login_entered, password_entered

            if self.__is_new_activity(app_package_name):
                self.__dprint("\n\n New Activity \n", self.__prev_act, "\n", self.__cur_act, '\n\n' )

                results = self.__detect()
                if not len(results.keys()):
                    return False, login_entered, password_entered

                tapped = False
                self.__dprint(f"Results: ", results)
            elif len(results.keys()) == 0 and empty_retries > 0:
                empty_retries -= 1
                self.__dprint("Empty results, grabbing new SS and processing...")
                sleep(3)
                # Get a new SS, ir error return
                results = self.__detect()
                if not len(results.keys()):
                    return False, login_entered, password_entered

            detect_attempt += 1
        return False, login_entered, password_entered
    # Old
    def __attempt_login(self, app_title: str, app_package_name: str, is_game: bool):
        # We need to press the submit buttton on the screen following the login
        # in order to use Facebook as an auth app for other apps like games.
        fb_login_continue_after_login = app_package_name == FACEBOOK_PACKAGE_NAME
        login_attemps = 0
        logged_in = False
        login_entered = False
        password_entered = False
        while not logged_in and login_attemps < 4:
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


    def __attempt_logins(self, app_title:str, package_name: str, is_game: bool):
        '''
            Attempts 3 login methods: Google, Facebook and Email/Password.
        '''
        has_google = has_facebook = has_email = False
        google_logged_in = facebook_logged_in = password_logged_in = False
        try:
            if is_game:
                sleep(5)
            p_alert("Attempting Google log in")
            google_logged_in, has_google = self.__handle_google_login(is_game, package_name)
        except Exception as error:
            p_alert("__handle_google_login: ", error)
            traceback.print_exc()
        try:
            clear_app(package_name, self.__device.info.transport_id)
            open_app(package_name, self.__device.info.transport_id, self.__device.info.arc_version)
            if is_game:
                sleep(5)
            p_alert("Attempting Facebook log in")
            facebook_logged_in, has_facebook = self.__handle_facebook_login(is_game, package_name)
        except Exception as error:
            p_alert("__handle_facebook_login: ", error)
            traceback.print_exc()
        try:
            clear_app(package_name, self.__device.info.transport_id)
            open_app(package_name, self.__device.info.transport_id, self.__device.info.arc_version)
            if is_game:
                sleep(5)
            p_alert("Attempting Email log in")
            password_logged_in, has_email = self.__handle_password_login(is_game, package_name)
        except Exception as error:
            p_alert("__handle_password_login: ", error)
            traceback.print_exc()

        return AppLoginResults(google_logged_in, has_google, facebook_logged_in, has_facebook, password_logged_in, has_email)
        # return [google_logged_in, facebook_logged_in, password_logged_in]

    ## PlayStore install discovery
    def login(self, app_title: str, app_package_name: str, app_info: AppInfo):
        ''' Attempts to log in to an app.
            TODO() implement behavior below.
            Args:
                - login_method: The method to use to login with.

            Returns:
                - dict containing the status of logged in and method used to log in.
        '''
        try:
            sleep(3)
            if app_package_name in SECURE_APPS.keys():
                creds = ACCOUNTS[app_package_name]
                # clear_app(app_package_name, self.__device.info.transport_id)
                # open_app(app_package_name, self.__device.info.transport_id, self.__device.info.arc_version)
                return SECURE_APPS[app_package_name](self.__driver, creds[0], creds[1])
            return self.__attempt_logins(app_title, app_package_name, app_info.is_game)
            # return self.__attempt_login(app_title, app_package_name, app_info.is_game)
        except Exception as error:
            p_alert(f"{self.__device.info.ip} - ", f"Error in login: {app_title} - {app_package_name}", error)
            traceback.print_exc()
        return [False, False, False]


if __name__ == "__main__":
    pass