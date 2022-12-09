import collections
from collections import defaultdict
import re
import subprocess
import sys
from time import sleep
from typing import AnyStr, Dict, List

import hashlib

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, ADB_KEYCODE_ENTER


def open_playstore():
    cmd = ('adb', 'shell', 'am', 'start', '-n', f'{PLAYSTORE_PACKAGE_NAME}/{PLAYSTORE_MAIN_ACT}')
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                            capture_output=True).stdout.strip()
    print("Starting playstore...")
    print(outstr)

def is_open(package_name: str) -> bool:
    cmd = ('adb', 'shell', 'pidof', package_name)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                            capture_output=True).stdout.strip()
    print(outstr)
    return len(outstr) > 0


def is_installed(package_name: str) -> bool: 
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



def discover_and_install(driver:webdriver.Remote, title: str, install_package_name: str):
    # try:
    # From Playstore home screen, click search icon
    search_icon = driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Search Google Play"]')	
    search_icon.click()

    # Send keys
    cmd = ( 'adb', 'shell', 'input', 'text', title)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    # Press enter to search for title
    cmd = ( 'adb', 'shell', 'input', 'keyevent', ADB_KEYCODE_ENTER)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()

    # Recognize Image
    # app_row_clickable = driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value='//android.view.View[@content-desc="Search Google Play"]')	
    



    ## Content desctiption
    content_desc = f'Image of app or game icon for {title}'
    app_icon = driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc)
    app_icon.click()
    
    
    content_desc = 'Install'
    install_BTN = driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc)
    install_BTN.click()

    # If we can find the size of the app before instal, we can try to determine the install time.
    sleep(15)
    sleep_cycle = 0
    while not is_installed(install_package_name) and sleep_cycle <= 20:
        sleep(2)
        print("Sleeping.... zzz")
        sleep_cycle += 1


    driver.back()  # back to seach results
    driver.back()  # back to home page


    print("App discovery and installation complete!")
    return True
    # except Exception as e:
    # NoSuchElementError
    #     driver.quit()
    #     print("Err: ", e)
    #     return False






if __name__ == "__main__":
    package = 'com.offerup'
    is_installed(PLAYSTORE_PACKAGE_NAME)
    open_playstore()
    is_open(PLAYSTORE_PACKAGE_NAME)