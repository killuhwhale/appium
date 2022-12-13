from collections import defaultdict
import collections
import re
import subprocess
from time import sleep, time
from typing import AnyStr, Dict, List

from appium import webdriver


from appium.webdriver.common.appiumby import AppiumBy

from selenium.common.exceptions import (StaleElementReferenceException, NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, ADB_KEYCODE_ENTER



''''
{
    package_name: {
        status: [pass | fail] int
        reason: "error message to produce fail status"
    }
}


'''

class ValidationReport:
    '''
        A simple class to format status report of AppValidator.
    '''
    PASS = 0
    FAIL = 1

    def __init__(self, report_title: str):
        self.report = collections.defaultdict(dict)
        self.report_title = ""

    def add(self, package_name: str, status: int, reason: str):
        self.report[package_name] = self.status_obj(status, reason)
    
    def status_obj(self, status: int, reason: str):
        return {
            'status': status,
            'reason': reason,
        }


    def print_report(self):
        # Sorted by packge name
        for package_name, status_obj in sorted(self.report.items(), key=lambda p: p[0]):
            is_good = status_obj['status'] == self.PASS 
            print(f"{package_name} search, install, open: {'PASSED' if is_good else 'FAILED'}")
            if not is_good:
                print(f"Failure: ", status_obj['reason'])



'''
Problems:

- Playstore will crash randomly....

- we need a strategy to handle this scenario.
    - Detect PlayStore closed.
    - Uninstall current app (Possibly has started to download)
    - Restart search/ discovery/ install process.



'''

class AppValidator:
    def __init__(self, driver: webdriver.Remote, package_names: List[List[str]]):
        self.driver = driver
        self.package_names = package_names  # List of packages to test as [app_title, app_package_name]
        self.report = ValidationReport("App discovery and Install")
        self.steps = [
            'Click search icon',
            'Send keys for search',
            'Click app icon',
            'Click install button',
        ]
        # Run session
        self.open_app(PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT)
        sleep(2)

    
    def run(self):
        for app_title, app_package_name in self.package_names:
            self.discover_and_install(app_title, app_package_name)
    
    def open_app(self, package_name: str, act_name: str):
        try:
            cmd = ('adb', 'shell', 'am', 'start', '-n', f'{package_name}/{act_name}')
            outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()
            print(f"Starting {package_name}/{act_name}...")
            print(outstr)
        except Exception as e:
            print("Error opening app")
            return False
        return True
    
    def is_open(self, package_name: str) -> bool:
        cmd = ('adb', 'shell', 'pidof', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(outstr)
        return len(outstr) > 0

    def is_installed(self, package_name: str) -> bool: 
        """Returns whether package_name is installed.
        Checks whether package_name is installed. package_name could be a
        partial name. Returns the full package name if only one entry matches.
        if more than one matches, it exits with an error.
        To avoid using partial name matches, -f should be used from command
        line.
        Args:
            package_name: A string representing the name of the application to
                be targeted.
        Returns:
            A string representing a validated full package name.
        """
        cmd = ('adb', 'shell', 'pm', 'list', 'packages')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()

        partial_pkg_regexp = fr'^package:(.*{re.escape(package_name)}.*)$'
        full_pkg_regexp = fr'^package:({re.escape(package_name)})$'

        regexp = full_pkg_regexp
        

        # IGNORECASE is needed because some package names use uppercase letters.
        matches = re.findall(regexp, outstr, re.MULTILINE | re.IGNORECASE)
        if len(matches) == 0:
            print(f'No installed package matches "{package_name}"')
            return False

        if len(matches) > 1:
            print(f'More than one package matches "{package_name}":')
            for p in matches:
                print(f' - {p}')
            return False

        print(f'Found package name: "{matches[0]}"')
        return True


    # 

    def is_installed_UI(self):
        '''
            Checks for the presence of the Uninstall button indicating that the app has completely finished installing.

            Using adb shows that the app is installed well before PlayStore UI says its ready to open.
        '''
        max_wait = 420  # 7 mins
        content_desc = 'Uninstall'
        ready = False
        t = time()
        while not ready and (time() - t) < max_wait:
            print("While")
            try:
                print("Searching for uninstall button....")
                uninstall_btn = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc)  # implicit wait time here, also
                print("Setting Ready to TRUE")
                ready = True
            except Exception as e:
                print("App not ready to open, sleeping 2s")
                sleep(2)
        return ready            
        
    def uninstall_multiple(self):
        for name in [pack_info[1] for pack_info in self.package_names]:
            self.uninstall_app(name)
        

    def uninstall_app(self, package_name: str):
        cmd = ( 'adb', 'uninstall', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        sleep(5)
        sleep_cycle = 0
        while self.is_installed(package_name) and sleep_cycle <= 20:
            sleep(2)
            print("Sleeping.... zzz")
            sleep_cycle += 1
        print(f"Took roughly {5 + sleep_cycle * 2} seconds.")

    def discover_and_install(self, title: str, install_package_name: str):
        ''' A method to search Google Playstore for an app and install via UI.
        
        '''
        try:
            last_step = 0  # track last sucessful step to, atleast, report in console.
            error = None
            # From Playstore home screen, click search icon
            search_icon = self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Search Google Play"]')	
            search_icon.click()
            # input("continue")

            last_step = 1
            # Send keys
            cmd = ( 'adb', 'shell', 'input', 'text', title.replace(" ", "\ "))
            outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
            # Press enter to search for title
            cmd = ( 'adb', 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

            last_step = 2
            ## Content desctiption
            # Image of app or game icon for Offerup: Buy. Sell. Letgo.
            content_desc = f'Image of app or game icon for {title}'.strip()
            
            # Old debug code,
            # print("Content desc matches target?", content_desc == target)
            # print("Searching content desc: ",)
            # print(target, len(target))
            # print(content_desc, len(content_desc))
            # for i in range(len(target)):
            #     a, b = ord(target[i]), ord(content_desc[i])
            #     if(not a== b):
            #         print(a,b)
            #         print(target[i], content_desc[i])
                

            sleep(2)
            # input("continue")
            app_icon = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc)
            app_icon.click()
            
            sleep(2)
            # input("continue")
            last_step = 3
            content_desc = 'Install'
            install_BTN = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc)
            install_BTN.click()

            # If we can find the size of the app before install, we can try to determine the install time.
            sleep(5)
            sleep_cycle = 0

            # Better install check would be to wait until the UI shows the "Uninstall button"
            #    	//android.view.View[@content-desc="Uninstall"]
            # Before the uninstall button, the cancel button will be present
            #    //android.view.View[@content-desc="Cancel"]

            if not self.is_installed_UI():
                raise Exception("Failed to find Unisntall button to verify ")
            

            
            # input("continue")
            self.driver.back()  # back to seach results
            self.driver.back()  # back to home page


            print("App discovery and installation complete!")
            return True
        except NoSuchElementException as e:
            error = e
        except Exception as e:
            error = e
        finally:
            if not error is None:
                self.report.add(install_package_name, ValidationReport.FAIL, error)
                print("Failed on step: ", last_step, self.steps[last_step])
                print("Err: ", error)
                self.driver.quit()
                return False
            else:
                self.report.add(install_package_name, ValidationReport.PASS, '')
                return True






if __name__ == "__main__":
    pass