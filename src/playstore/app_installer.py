from dataclasses import dataclass
import re
import subprocess
from time import sleep, time
import traceback
from typing import List, Tuple
import __main__
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from utils.app_utils import is_installed, uninstall_app
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import get_color_printer, p_alert
from utils.utils import (ADB_KEYCODE_ENTER, PLAYSTORE_PACKAGE_NAME)


class NeedsPurchaseException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class NeedsUpdateException(Exception):
    pass

class NotInstalledException(Exception):
    pass

class FoundWrongPackageException(Exception):
    pass

class FailedClickIconException(Exception):
    pass

class PlaystoreCrashException(Exception):
    pass

class PlaystoreANRException(Exception):
    pass

class PlaystoreInstallFailedException(Exception):
    pass

@dataclass
class AppInstallerResult:
    installed: bool
    message: str
    price: float = 0.0



class AppInstaller:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.
    '''
    def __init__(
            self,
            driver: webdriver.Remote,
            device: Device,
            dprinter
        ):
        self.__driver = driver
        self.__device = device.info
        self.__ip = self.__device.ip
        self.__transport_id = self.__device.transport_id
        self.__arc_version = self.__device.arc_version
        self.__is_emu = self.__device.is_emu
        self.__err_detector = ErrorDetector(device.info, self.__arc_version)

        self.__steps = [
            'Click search icon',
            'Send keys for search',
            'Click app icon',
            'Click install button',
        ]
        self.__dprint = dprinter

    def uninstall_multiple(self):
        for app_info in self.__package_names:
            package_name = app_info[1]
            uninstall_app(package_name)

    ##  Buttons
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



    def __return_error(self, last_step: int, error: str):
        if last_step == 0:
            self.__driver.back()
            # return [False, f"Failed: {self.__steps[0]}"]
            return AppInstallerResult(False, f"Failed: {self.__steps[0]}")
        elif last_step == 1:
            self.__driver.back()
            # return [False, f"Failed: {self.__steps[1]}"]
            return AppInstallerResult(False, f"Failed: {self.__steps[1]}")
        elif last_step == 2:
            self.__driver.back()
            # return [False, f"Failed: {self.__steps[2]}"]
            return AppInstallerResult(False, f"Failed: {self.__steps[2]}")
        elif last_step == 3:
            self.__driver.back()
            self.__driver.back()
            self.__dprint(f"Failed: {self.__steps[3]} :: {error}")
            # return [False, f"Failed: {self.__steps[3]} :: {error}"]
            return AppInstallerResult(False, f"Failed: {self.__steps[3]} :: {error}")

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
                self.__dprint("Found first uninstall button....")
                self.__dprint("Setting Ready to TRUE")
                ready = True
                break
            except Exception as e:
                self.__dprint("App not ready to open, retrying...")
                sleep(0.5)

            try:
                self.__driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Uninstall")
                self.__dprint("Found second uninstall button....")
                ready = True
            except Exception as e:
                self.__dprint("App not ready to open, retrying...")
                if t > max_wait * 0.25:
                    self.__check_playstore_crash()
                    self.__check_playstore_anr()
                    self.__check_playstore_install_fail()
                sleep(0.5)
            self.__driver.orientation = 'PORTRAIT'
        return ready

    def __needs_purchase(self) -> float:
        try:
            content_desc = f'''
                new UiSelector().className("android.widget.Button").textMatches(\"\$\d+\.\d+\")
            '''
            self.__dprint("Searching for Button with Price...", content_desc)
            btn = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            price = btn.text
            print(f"A {price=}")
            return float(price.replace("$", ''))
        except Exception as e:
            print("failed ", e)
        try:
            content_desc = f'''new UiSelector().descriptionMatches(\"\$\d+\.\d+\");'''
            self.__dprint("Searching for Button with Price...", content_desc)
            btn = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            price = btn.get_attribute('content-desc')
            return float(price.replace("$", ''))
        except Exception as e:
            print("failed ", e)
        return 0.0

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
        try:
            content_desc = f'''
                new UiSelector().className("android.widget.TextView").text("Search for apps & games")
            '''
            search_icon = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            search_icon.click()
            self.__dprint("Search icon clicked.")
        except Exception as error:
            # Playstore version Eve (4-13-2023): version 35.2.19-21 [0] [PR] 522404461
            content_desc = f'''
                new UiSelector().className("android.widget.TextView").text("Search apps & games")
            '''
            search_icon = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            search_icon.click()
            self.__dprint("Second search icon clicked.")

    def __check_playstore_crash(self):
        # 01-05 22:08:57.546   129   820 I WindowManager: WIN DEATH: Window{afca274 u0 com.android.vending/com.google.android.finsky.activities.MainActivity}
        # cur_package = self.__err_detector.get_package_name()
        # self.__err_detector.update_package_name(PLAYSTORE_PACKAGE_NAME)
        # self.__err_detector.update_package_name(cur_package)  # switch back to package

        errors = self.__err_detector.check_crash()
        print(f"{errors=}")
        if(not CrashTypes.SUCCESS in errors):
            all_errors_msg = []
            for key, val in errors.items():
                crash_type, crashed_act, msg = val
                all_errors_msg.append(crash_type.value)
            self.__dprint("PlayStore crashed ", ' '.join(all_errors_msg))
            raise PlaystoreCrashException()
        return False

    def __check_playstore_anr(self):
        try:
            self.__dprint("Checking playtore ANR")
            content_desc = f'''new UiSelector().text("Wait")'''
            wait_button = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
            wait_button.click()
            self.__dprint("PlayStore stopped responding")
            raise PlaystoreANRException()
        except Exception as e:
            self.__dprint("No ANR found")
            # self.__dprint("Playstore ANR error: ", e) # Failed to find ANR, no need to report error.
        return False

    def __check_playstore_install_fail(self):
        try:
            self.__dprint("Check playstore install fail")
            feedback_desc = f'''new UiSelector().className("android.widget.Button").text("Send feedback")'''
            got_it_desc = f'''new UiSelector().className("android.widget.Button").text("Got it")'''
            feedback_button = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=feedback_desc)
            got_it_button = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=got_it_desc)
            if feedback_button and got_it_button:
                got_it_button.click()
            self.__dprint("PlayStore couldn't install application")
            raise PlaystoreInstallFailedException()
        except Exception as e:
            self.__dprint("No app install fail found.")
        return False

    def __search_playstore(self, title: str, submit=True):
        content_desc = f'''
            new UiSelector().className("android.widget.EditText")
        '''
        search_edit_text = self.__driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        search_edit_text.send_keys(title)
        if submit:
            cmd = ( 'adb', '-t', self.__transport_id, 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        sleep(2)  # Wait for search results

    def __find_coords(self, bounds: List[int]) -> Tuple[str]:
        '''
            bounds='[276,297][1883,475]'
        '''
        print(f"{bounds=}")
        x = ((bounds[2] - bounds[0]) // 2) + bounds[0]
        y = ((bounds[3] - bounds[1]) // 2) + bounds[1]
        return (str(x), str(y),)

    def __click_app_icon(self, title: str, package_name: str):
        '''
            # Sometime the app has a different view on the same device.
            contentdesc = App: My Boy! - GBA Emulator Fast Emulator Arcade Star rating: 4.6 1,000,000+ downloads $4.99

            Emulator:
                Image of app or game icon for Roblox
        '''

        title_first = title
        self.__dprint(f"Searching for clickable element: {title_first}")
        descs = [
            f'''new UiSelector().className("android.widget.TextView").text("{title_first}");''',
            f'''new UiSelector().textMatches(\"(?i){title_first}.*\");'''
            f'''new UiSelector().descriptionMatches(\".*(?i){title_first}.*\");''', # Pixel 2
            f'''new UiSelector().descriptionMatches(\"App: (?i){title_first}.*\");''',  # Chromebooks
            f'''new UiSelector().descriptionMatches(\"(?i){title_first}.*\");''',
            # f'''new UiSelector().descriptionMatches(\"App: (?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \| \\n]*\");''',  # Chromebooks
            # f'''new UiSelector().descriptionMatches(\"(?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \| \\n]*\");''',
            # f'''new UiSelector().textMatches(\"(?i){title_first}[a-z A-Z 0-9 \. \$ \, \+ \: \! \- \- \| \\n]*\");'''
        ]
        for content_desc in descs:
            self.__dprint("Searhing for app_icon with content desc: ", content_desc)
            try:
                app_icon = self.__driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
                for icon in app_icon:

                    cont_desc = icon.get_attribute('content-desc')
                    self.__dprint("Icons:", icon.location, icon.id, cont_desc)
                    if ("Image" in cont_desc or title_first in cont_desc or not cont_desc) and not "Play trailer" in cont_desc:
                        self.__dprint("Clicked: ", icon.id, cont_desc)
                        bounds = icon.get_attribute("bounds")
                        # icon.click()  # NOTE bug on Eve, Caroline it wont click the app icon to get into the detail view.
                        # Trial and error: this has been working without issues...
                        self.__tap_screen(*self.__find_coords(self.__extract_bounds(bounds)))
                        self.__tap_screen(*self.__find_coords(self.__extract_bounds(bounds)))
                        sleep(1)
                        return
            except Exception as e:
                self.__dprint("❌ Icon failed click ", e)
        raise FailedClickIconException()

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
        first_method_clicked = False
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
                first_method_clicked = True
                self.__dprint("Clicked first install")

            except Exception as error:
                self.__dprint("First install method failed.")

            if not first_method_clicked:
                content_desc = f'''
                    new UiSelector().className("android.widget.Button").text("Install")
                '''
                self.__dprint(f"First failed, now Looking at {content_desc=}")
                install_BTN = self.__driver.find_element(
                    by=AppiumBy.ANDROID_UIAUTOMATOR,
                    value=content_desc)
                install_BTN.click()
                self.__dprint("Clicked second install")

        except Exception as e:  # Install btn not found
            err = True
            self.__dprint("Failed to find any install button on transport id: ", self.__transport_id, e)
            already_installed = is_installed(install_package_name, self.__transport_id)

        # Error finding/Clicking Install button and app is not installed still...
        if err and not already_installed:
            self.__dprint("Verifying UI for Needs to Purchase...")
            price = self.__needs_purchase()
            print(f"{price=}")
            if price:
                self.__dprint("raising needs purchase")
                raise NeedsPurchaseException(str(price))

            if self.__needs_update():
                self.__dprint("raising needs update")
                raise NeedsUpdateException()

            # Now, Install and Price, Update are not present,
            # To get here, we must be looking for a package
            # com.abc.foogame
            # When we search by name, foogame,
            # The app foogame, by com.zyx.foogames is actually showing.
            # So we check if the packge is installed via ADB cmd because this will be a source of truth
            # Therefore, at this point we have an installed app, that doesnt match our targeted package name.
            # NOTE: On the first run, it will install this package and report as correct....
            self.__dprint(f"Program may have installed an incorrect package, {install_package_name} was not actually installed")
            #  Exception(f"{install_package_name} was not installed.")
            raise NotInstalledException()

        # We have successfully clicked an install buttin
        # We wait for it to download. We will catch if its the correct package or not after installation.
        if not self.__is_installed_UI():  # Waits up to 7mins to find install button.
            # raise Exception("Failed to install app!!")
            raise FoundWrongPackageException()

    def __discover_and_install(self, title: str, install_package_name: str):
        '''
         A method to search Google Playstore for an app and install via the Playstore UI.
        '''
        try:
            last_step = 0  # track last sucessful step to, atleast, report in console.
            self.__click_playstore_search()
            self.__check_playstore_crash()
            self.__check_playstore_anr()
            self.__check_playstore_install_fail()

            last_step = 1
            self.__search_playstore(title)
            self.__check_playstore_crash()
            self.__check_playstore_anr()
            self.__check_playstore_install_fail()

            last_step = 2
            self.__click_app_icon(title, install_package_name)
            self.__check_playstore_crash()
            self.__check_playstore_anr()
            self.__check_playstore_install_fail()

            last_step = 3
            self.__install_app_UI(install_package_name)
            self.__check_playstore_crash()
            self.__check_playstore_anr()
            self.__check_playstore_install_fail()
            self.__driver.back()  # back to seach results
            self.__driver.back()  # back to home page
        except PlaystoreCrashException as e:
            raise PlaystoreCrashException()
        except NeedsPurchaseException as price:
            error = self.__return_error(last_step, "Needs purchase.")
            error.price = float(price.message)
            return error
        except NeedsUpdateException:
            return self.__return_error(last_step, "Needs update.")
        except NotInstalledException:
            return self.__return_error(last_step, "Not installed.")
        except FoundWrongPackageException:
            return self.__return_error(last_step, "Wrong package found in playstore.")
        except FailedClickIconException:
            return self.__return_error(last_step, 'Failed to click app icon.')
        except PlaystoreANRException as error:
            return self.__return_error(last_step, error)
        except PlaystoreInstallFailedException as error:
            return self.__return_error(last_step, error)
        except Exception as error:
            print("General failure in installer: ", error)
            traceback.print_exc()
            return self.__return_error(last_step, error)
        return AppInstallerResult(True, "")

    def discover_and_install(self, app_title: str, app_package_name: str) -> List:
        try:
            return self.__discover_and_install(app_title, app_package_name)
        except PlaystoreCrashException:
            self.__dprint("Playstore crashed!")  # Havent encountered this in a long time.
            return AppInstallerResult(False, f"Failed: Playstore crashed")
        except Exception as error:
            p_alert(f"{self.__ip} - ", f"Error in isntaller RUN: {app_title} - {app_package_name}", error)
            traceback.print_exc()
            return AppInstallerResult(False, f"Failed: {error=}")

if __name__ == "__main__":
    pass