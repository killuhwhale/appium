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

from utils.utils import ADB_KEYCODE_ENTER, open_app, close_app


class Launcher:
    '''
        Laucnhes apps to test them
    '''

    def __init__(self, package_names: List[str]):
        self.package_names = [pack_info[1] for pack_info in package_names]
    

    def run(self):
        for name in self.package_names:
            open_app(name)
            print("Loggin in to: ", name)
            # Login
            # Logout? This is hard for users sometimes...

            # Need to wait for app to finish launching....
            # We need to detect splash screens
            # We need to detect Username/Email and Password fields

            
            input("Close app")
            close_app(name)

