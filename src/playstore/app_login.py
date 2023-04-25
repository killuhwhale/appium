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
from utils.app_utils import AppInfo, check_and_close_smartlock, clear_app, close_app, get_cur_activty, get_root_path, is_download_in_progress, open_app
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import get_color_printer, p_alert
from utils.secure_app_logins import SECURE_APPS
from utils.utils import (ADB_KEYCODE_ENTER, CONTINUE,
                         FACEBOOK_PACKAGE_NAME, FB_ATUH, GOOGLE_AUTH, LOGIN,
                         PASSWORD, V8_WEIGHTS, WEIGHTS, save_resized_image, transform_coord_from_resized)


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
            error_detector: ErrorDetector,
            dprinter
        ):
        self.__driver = driver
        self.__device = device
        self.__report = report
        self.__err_detector = error_detector
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

        coords = transform_coord_from_resized(
            (self.__device.info.wxh),
            (1920, 1080),
            (int(x), int(y))
        )
        return str(int(coords[0])), str(int(coords[1]))
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
            # resized = src.resize((640,640))  # BICUBIC by default
            resized = src.resize((1920,1080), resample=Image.BILINEAR)  # letterbox mimic like Roboflow
            # resized_final = resized.resize((640,640), resample=Image.BILINEAR)  # letterbox mimic like Roboflow
            # src.resize((640,640), resample=Image.LANCZOS)
            end = perf_counter()
            print(f"\n\n Getting image and resizing took: {(end - start):.6f}s \n\n")
            return self.__detector_v8.detect(resized)
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


    def __handle_google_login(self, is_game: bool, app_package_name: str) -> List[bool]:
        ''' Looks for Google Auth buttons and Continue buttons until reaching Google Auth button.

            Clicks on account within GAuth dialogs.

            Returns:
                - True when Gauth is found and email is successfully clicked.
        '''
        GOOGLE_SUBMITTED = False
        has_google = False
        empty_retries = 2
        attempts = 3
        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not GOOGLE_SUBMITTED and empty_retries >= 0 and attempts > 0:
            attempts -= 1
            check_and_close_smartlock(self.__driver)
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
                print("Current GAuth act: ", self.__driver.current_activity)
                print(f"{(app_package_name in ACCOUNTS)=}")
                if self.__driver.current_activity == '.common.account.AccountPickerActivity' and app_package_name in ACCOUNTS:
                    login_val = ACCOUNTS[app_package_name][0]

                    content_desc = f'''new UiSelector().className("android.widget.TextView").text("{login_val}")'''
                    print(f"Clicking google w/ {content_desc=}")
                    self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
                    self.__report.add_history(app_package_name, "Google Auth sign-in", self.__driver)
                    GOOGLE_SUBMITTED = True
                    self.__dprint("Logged in Google!")
                    return True, has_google
                else:
                    p_alert(f"{self.__device.info.ip} - Found Google Auth login but not associated account for {app_package_name=} {(app_package_name in ACCOUNTS)=} or perhaps wrong actiity showing, which we need to extend overage... {self.__driver.current_activity=}")

            elif CONTINUE in results:
                print("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                print("App is game: ", is_game)
                if is_game:
                    sleep(1)
                    self.__sleep_while_in_progress(app_package_name)

        return False, has_google

    def __handle_facebook_login(self, is_game: bool, app_package_name: str) -> List[bool]:
        ''' Looks for Facebook Auth buttons and Continue buttons until reaching Facebook Auth button.

            Clicks on account within FacebookAuth dialogs.

            Returns:
                - True when Facebook auth is found and email is successfully clicked.
        '''
        FACEBOOK_SUBMITTED = False
        has_facebook = False
        empty_retries = 2
        attempts = 3
        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not FACEBOOK_SUBMITTED and empty_retries >= 0 and attempts >=0:
            attempts -= 1
            check_and_close_smartlock(self.__driver)
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
                self.__dprint("Logged in Facebook!")
                return True, has_facebook


            elif CONTINUE in results:
                print("Click Continue        <-------")
                results[CONTINUE], tapped = self.__click_button(results[CONTINUE])
                self.__clean_result(CONTINUE, results)

                print("App is game: ", is_game)
                if is_game:
                    sleep(1)
                    self.__sleep_while_in_progress(app_package_name)
        return False, has_facebook


    def __handle_password_login(self, is_game: bool,
                              app_package_name: str) -> List[bool]:

        login_entered = password_entered = False
        CONTINUE_SUBMITTED = False
        has_email = False
        empty_retries = 5
        attemtps = 7 # When a detect occurs on a non-clickable element, we need to break from the loop

        print("App is game: ", is_game)
        if is_game:
            sleep(5)
            self.__sleep_while_in_progress(app_package_name)

        while not (CONTINUE_SUBMITTED and login_entered and password_entered) and empty_retries > 0 and attemtps >= 0:
            attemtps -= 1
            print("Password login attempts left: ", attemtps)
            if CONTINUE_SUBMITTED and login_entered and password_entered:
                return True, has_email

            check_and_close_smartlock(self.__driver)

            results: defaultdict = self.__detect()
            self.__dprint(f"Results: ", results)
            if not len(results.keys()):
                empty_retries -= 1
                sleep(5)
                if empty_retries == 0:
                    return False, has_email

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
                    p_alert(f"{self.__device.info.ip} - Login info not created for {app_package_name} but found an email/password login")
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
                    p_alert(f"{self.__device.info.ip} - Password info not created for {app_package_name} but found an email/password login")
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
                    self.__dprint("Logged in Email!")
                    return True, has_email

        return False, has_email

    def __get_login_methods(self, package_name):
        email_only = []
        facebook_only = ['com.dts.freefireth']
        google_only = ['com.facebook.katana']
        if package_name in google_only:
            return [self.__handle_google_login, None, None]
        if package_name in facebook_only:
            return [None, self.__handle_facebook_login, None]
        if package_name in email_only:
            return [None, None, self.__handle_password_login]


    def __attempt_logins(self, app_title:str, package_name: str, is_game: bool):
        '''
            Attempts 3 login methods: Google, Facebook and Email/Password.
        '''
        login_methods = self.__get_login_methods(package_name)
        login_result = AppLoginResults(error_detected=True)
        for i, login_method in enumerate(login_methods):
            if not login_method: continue
            try:
                if i > 0:
                    close_app(package_name, self.__device.info.transport_id)
                    clear_app(package_name, self.__device.info.transport_id)
                    open_app(package_name, self.__device.info.transport_id, self.__driver, self.__device.info.arc_version)
                    self.__err_detector.reset_start_time()
                if is_game:
                    sleep(10)
                p_alert(f"{self.__device.info.ip} - Attempting {login_method.__name__}")

                logged_in, has_login = login_method(is_game, package_name)
                login_result.update_field(i, logged_in, has_login)

                errors = self.__err_detector.check_crash()
                if(not CrashTypes.SUCCESS in errors):
                    login_result.error_detected = True



            except Exception as error:

                p_alert(f"{self.__device.info.ip} - {login_method.__name__}: ", error)
                traceback.print_exc()
        # return AppLoginResults(*raw_results)
        return login_result

    ## PlayStore install discovery
    def login(self, app_title: str, app_package_name: str, app_info: AppInfo):
        ''' Attempts to log in to an app.
            Args:
                - login_method: The method to use to login with.

            Returns:
                - dict containing the status of logged in and method used to log in.
        '''
        try:
            sleep(3)
            if app_package_name in SECURE_APPS.keys():
                creds = ACCOUNTS[app_package_name]
                return SECURE_APPS[app_package_name](self.__driver, creds[0], creds[1])
            return self.__attempt_logins(app_title, app_package_name, app_info.is_game)
        except Exception as error:
            p_alert(f"{self.__device.info.ip} - ", f"Error in login: {app_title} - {app_package_name}", error)
            traceback.print_exc()
        return AppLoginResults(*[False]*6)


if __name__ == "__main__":
    pass