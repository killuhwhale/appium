from collections import defaultdict
import collections
import re
import subprocess
from time import sleep, time
from typing import AnyStr, Dict, List
import math
from appium import webdriver


from appium.webdriver.common.appiumby import AppiumBy

from selenium.common.exceptions import (StaleElementReferenceException, NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, ADB_KEYCODE_ENTER, close_app, open_app



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
        RED,
        Black,
        Green,
        Yellow,
        Blue,
        Purple,
        Cyan,
        White,
    ]

    REPEAT_TIMES = 10*len(COLORS)


    def __init__(self, report_title: str):
        self.report = collections.defaultdict(lambda: {"empty": 1})
        self.report_title = ""
        self.anim_starting()

    def add(self, package_name: str, app_name: str, status: int, reason: str):
        ''' Add report of a pacage if a report DNExist'''
        if "empty" in self.report[package_name]:
            self.report[package_name] = self.status_obj(status, reason, app_name)
    
    def gen_sine(self):
        sine_wave = []
        for i in range(self.REPEAT_TIMES):
            angle = i * 2 * math.pi / 80  # convert i to an angle in radians
            value = math.sin(angle)  # calculate the sine of the angle
            value = (value + 1) / 2  # scale the value to a range between 0 and 1
            sine_wave.append(value)  # add the scaled value to the list
        
        return sine_wave


    def status_obj(self, status: int, reason: str, name: str):
        return {
            'status': status,
            'reason': reason,
            'name': name,
        }

    def ascii_footer(self):
        print(self.Green)
        
        print('''
               _  _     _  _     _  _     _   ___ _ _       _       _    _ _           _  _____     _  _     _  _     _  _   
             _| || |_ _| || |_ _| || |_  | | / (_) | |     | |     | |  | | |         | ||____ |  _| || |_ _| || |_ _| || |_ 
            |_  __  _|_  __  _|_  __  _| | |/ / _| | |_   _| |__   | |  | | |__   __ _| |    / / |_  __  _|_  __  _|_  __  _|
             _| || |_ _| || |_ _| || |_  |    \| | | | | | | '_ \  | |/\| | '_ \ / _` | |    \ \  _| || |_ _| || |_ _| || |_ 
            |_  __  _|_  __  _|_  __  _| | |\  \ | | | |_| | | | | \  /\  / | | | (_| | |.___/ / |_  __  _|_  __  _|_  __  _|
              |_||_|   |_||_|   |_||_|   \_| \_/_|_|_|\__,_|_| |_|  \/  \/|_| |_|\__,_|_|\____/    |_||_|   |_||_|   |_||_|                                                                                             
        ''')
        print(self.RESET)
        
    
    def ascii_header(self):
        print(self.Green)
        print(f'''
              _  _     _  _     _  _    ______                      _       _  _     _  _     _  _   
            _| || |_ _| || |_ _| || |_  | ___ \                    | |    _| || |_ _| || |_ _| || |_ 
           |_  __  _|_  __  _|_  __  _| | |_/ /___ _ __   ___  _ __| |_  |_  __  _|_  __  _|_  __  _|
            _| || |_ _| || |_ _| || |_  |    // _ \ '_ \ / _ \| '__| __|  _| || |_ _| || |_ _| || |_ 
           |_  __  _|_  __  _|_  __  _| | |\ \  __/ |_) | (_) | |  | |_  |_  __  _|_  __  _|_  __  _|
             |_||_|   |_||_|   |_||_|   \_| \_\___| .__/ \___/|_|   \__|   |_||_|   |_||_|   |_||_|  
                                                | |                                                
                                                |_|                                                                 
        ''')
        print(self.RESET)


    def anim_starting(self):
        print("\033[2J")  # clear the screen
        sine_wave = self.gen_sine()
        for i in range(len(sine_wave)):
            color = self.COLORS[i % 3]
            print("\033[0;0H")  # move cursor to top-left corner
            self.ascii_starting(color)
            sleep(sine_wave[i]/5)

    def ascii_starting(self, color=None):
        if color is None:
            color = self.Green
        print(color)
        print(f'''
              _  _     _  _     _  _     _____ _             _   _                         _  _     _  _     _  _   
            _| || |_ _| || |_ _| || |_  /  ___| |           | | (_)                      _| || |_ _| || |_ _| || |_ 
           |_  __  _|_  __  _|_  __  _| \ `--.| |_ __ _ _ __| |_ _ _ __   __ _          |_  __  _|_  __  _|_  __  _|
           _| || |_ _| || |_ _| || |_   `--. \ __/ _` | '__| __| | '_ \ / _` |          _| || |_ _| || |_ _| || |_ 
          |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |  | |_| | | | | (_| |  _ _ _  |_  __  _|_  __  _|_  __  _|
            |_||_|   |_||_|   |_||_|   \____/ \__\__,_|_|   \__|_|_| |_|\__, | (_|_|_)   |_||_|   |_||_|   |_||_|  
                                                                         __/ |                                     
                                                                        |___/                                      
        ''')
        print(self.RESET)


    def print_report(self):
        # Sorted by packge name
        self.ascii_header()
        for package_name, status_obj in sorted(self.report.items(), key=lambda p: p[0]):
            is_good = status_obj['status'] == self.PASS 
            print(self.Blue, end="")
            print(f"{status_obj['name']} ", end="")
            print(self.RESET, end="")
            print(f"{package_name} search/install status: ", end="")
            if is_good:
                print(self.Green, end="")
                print("PASSED")
                print(self.RESET, end="")

            else:
                print(self.RED, end="")
                print("FAILED")
                print("\n\t\t", status_obj['reason'])
                print(self.RESET, end="")
            print()
        self.ascii_footer()


'''
Problems:

- Playstore will crash randomly....

- we need a strategy to handle this scenario.
    - Detect PlayStore closed.
    - Uninstall current app (Possibly has started to download)
    - Restart search/ discovery/ install process.
'''

class AppValidator:
    ''' TODO
     GetSize
     - use uiautomator regex to find 73% of 581 MB | KB pattern to get the digits between 'of' and either MB or KB.
    
    '''

    PICUTRES = "/home/killuh/Pictures"
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
        # Open Playstore 
        # self.open_app(PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT)
        # sleep(2)

    
    def run(self):
        '''
            Main loop of the Playstore class, starts the cycle of discovering, 
            installing, logging in and uninstalling each app from self.package_names.

            It ensures that the playstore is open at the beginning and that
            the device orientation is returned to portrait.
        '''
        for app_title, app_package_name in self.package_names:
            ERR = False
            installed, error = self.discover_and_install(app_title, app_package_name)

            if not installed and not error is None:
                self.report.add(app_package_name, app_title, ValidationReport.FAIL, error)
                ERR = True
                continue
            
            if not open_app(app_package_name):
                ERR = True
                self.report.add(app_package_name, app_title, ValidationReport.FAIL, "Failed to open")

            # TODO wait for activity to start intelligently, not just package
            # DEV: Using to scrape the first image of each app. (Will remove)
            if not ERR:
                sleep(8)  # Wait for app to finsh loading the "MainActivity"
                self.report.add(app_package_name, app_title, ValidationReport.PASS, '')
                _app_title = app_title.replace(" ", "_")
                self.driver.get_screenshot_as_file(f"{self.PICUTRES}/{_app_title}.png")

            # TODO Do login, building obj detection            
            # input("Close app")            
            close_app(app_package_name)
            
            # Change the orientation to portrait
            self.driver.orientation = 'PORTRAIT'

            # TODO Make sure PlayStore is in ForeGround and back to portrait ori
            # Uninstall app (save space when doing hundreds of apps)
            self.uninstall_app(app_package_name)
    
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
        Args:
            package_name: A string representing the name of the application to
                be targeted.
        Returns:
            A boolean representing if package is installed.
        """
        cmd = ('adb', 'shell', 'pm', 'list', 'packages')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
            capture_output=True).stdout.strip()
        full_pkg_regexp = fr'^package:({re.escape(package_name)})$' ## for partial surround like: .*{}.*
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

    def is_installed_UI(self):
        '''
            Checks for the presence of the Uninstall button indicating that the app has completely finished installing.

            Using adb shows that the app is installed well before PlayStore UI says its ready to open.
        '''
        max_wait = 420  # 7 mins, Large gaming apps may take a while to download.
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
        uninstalled = False
        try:
            cmd = ( 'adb', 'uninstall', package_name)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
            sleep(5)
            uninstalled = True
        except Exception as e:
            print("Error uninstalling: ", package_name, e)
        
        if uninstalled:
            try:
                sleep_cycle = 0
                while self.is_installed(package_name) and sleep_cycle <= 20:
                    sleep(2)
                    print("Sleeping.... zzz")
                    sleep_cycle += 1
                print(f"Took roughly {5 + sleep_cycle * 2} seconds.")
            except Exception as e:
                print("Error checking is installed after uninstall: ", package_name, e)

    def escape_chars(self, title: str):
        title_search = title.replace("'", "\\'")
        title_search = title_search.replace(" ", "\ ")
        title_search = title_search.replace('"', '\\"')
        title_search = title_search.replace("&", "\&")
        return title_search

    def return_error(self, last_step):
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
            return [False, f"Failed: {self.steps[3]}"]

    def click_playstore_search(self):
        # From Playstore home screen, click search icon
        search_icon = self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Search Google Play"]')	
        search_icon.click()

    def send_keys_playstore_search(self, title: str):
        title_search = self.escape_chars(title)
        print("Searching: ", title_search)
        cmd = ( 'adb', 'shell', 'input', 'text', title_search)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        cmd = ( 'adb', 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        sleep(2)

    def press_app_icon(self, title: str):
        title_first = title.split(" ")[0]
        content_desc = f'''new UiSelector().descriptionMatches(\"Image of app or game icon for .*{title_first}.*\");'''
        print("Searhing for app_icon with content desc: ", content_desc)
        app_icon = self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc)
        app_icon.click()
        sleep(2)

    def install_app_UI(self, install_package_name: str):
        already_installed = False  # Potentailly already isntalled
        try:
            install_BTN = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value='Install')
            install_BTN.click()
        except Exception as e:  # Install btn not found
            already_installed = self.is_installed(install_package_name)
                    
        if not already_installed:
            print("Verifying if installed already...")
            if not self.is_installed_UI():
                raise("Failed to find Unisntall button to verify ")
            else:
                print("App already installed...")


    def discover_and_install(self, title: str, install_package_name: str):
        '''
         A method to search Google Playstore for an app and install via the Playstore UI.
        '''
        try:
            last_step = 0  # track last sucessful step to, atleast, report in console.
            error = None

            last_step = 1
            self.send_keys_playstore_search(title)

            last_step = 2
            self.press_app_icon(title)

            last_step = 3
            self.install_app_UI(install_package_name)
                    
            self.driver.back()  # back to seach results
            self.driver.back()  # back to home page
        except Exception as e:
            error = e
        finally:
            if error is None:
                return [True, None]
            else:
                # Debug
                print("\n\n", title, install_package_name, "Failed on step: ", last_step, self.steps[last_step])
                # input('Error')  # Debug
                return self.return_error(last_step)






if __name__ == "__main__":
    pass