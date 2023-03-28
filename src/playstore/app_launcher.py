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
from playstore.app_installer import AppInstaller
from playstore.app_login import AppLogin
from playstore.validation_report import ValidationReport
from utils.app_utils import AppInfo, close_app, create_dir_if_not_exists, get_cur_activty, get_root_path, is_download_in_progress, is_installed, open_app
from utils.device_utils import Device
from utils.error_utils import CrashTypes, ErrorDetector
from utils.logging_utils import AppLogger, get_color_printer, p_alert, p_blue, p_cyan, p_green, p_purple, p_red, p_yellow
from utils.utils import (ACCOUNTS, ADB_KEYCODE_ENTER, CONFIG,
                         CONTINUE,  FACEBOOK_APP_NAME,
                         FACEBOOK_PACKAGE_NAME, FB_ATUH, GOOGLE_AUTH,
                         LOGIN, PASSWORD, PLAYSTORE_PACKAGE_NAME, WEIGHTS)

class AppLauncher:
    ''' Main class to validate a broken app. Discovers, installs, opens and
          logs in to apps.
    '''
    def __init__(
            self,
            device: Device,
            app_list_queue: Queue,
            instance_num

        ):
        self.__report = ValidationReport(device)
        self.__app_list_queue = app_list_queue

        self.__device = device.info
        self.__transport_id = self.__device.transport_id
        self.__arc_version = self.__device.arc_version

        self.__name_span_text = ''
        self.__misnamed_reason_text = "App name does not match the current name on the playstore."
        self.dev_ss_count = 8
        self.__dprint = get_color_printer(instance_num)

    @property
    def report(self):
        return self.__report

    def __check_playstore_invalid(self, package_name) -> bool:
        ''' Checks if an app's package_name is invalid via Google playstore URL
            If invalid, returns True
            If valid, returns False
        '''

        url = f'https://play.google.com/store/apps/details?id={package_name}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
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

        elif not is_installed(package_name, self.__device.transport_id):
            reason = f"Not installed - {msg}"
        else:
            reason = msg
        return NEW_APP_NAME, INVALID_APP, reason

    def check_open_app(self, app_title: str, package_name: str):
        if not open_app(package_name, self.__transport_id, self.__arc_version):
            new_app_name, invalid_app, reason = self.__handle_failed_open_app(package_name, app_title, "Failed to open")
            return [False, new_app_name, invalid_app, reason]
        return [True, "", False, "" ]


if __name__ == "__main__":
    pass