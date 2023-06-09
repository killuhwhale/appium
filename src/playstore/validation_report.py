import collections
from enum import Enum
from appium.webdriver import Remote
from copy import deepcopy
from typing import Dict, List
import __main__
from playstore.app_login import AppLoginResults
from utils.app_utils import AppData, create_dir_if_not_exists, get_root_path
from utils.device_utils import Device
from utils.logging_utils import ( p_blue, p_cyan, p_green,
                         p_purple, p_red, p_yellow)
from utils.utils import AppStatus



class ValidationReport:
    '''
        A simple class to format the status report of AppValidator.
         = {
            report_title: {
                package_name: {
                    'status': -1,
                    'name': "",
                    'report_title': "",
                    'history': [],
                    'logs', '',
                },
                ...,
            },
            report_title2: {
                package_name: {
                    'status': -1,
                    'name': "",
                    'report_title': "",
                    'history': [],
                    'logs', '',
                },
                ...,
            }
        }
    '''
    # LOGGED_IN_FACEBOOK = -3
    # LOGGED_IN_GOOLE = -2
    # LOGGED_IN_EMAIL = -1
    # PASS = 0
    # FAIL = 1
    # CRASH_WIN_DEATH = 2
    # CRASH_FORCE_RM_ACT_RECORD = 3
    # CRASH_ANR = 4
    # CRASH_FDEBUG_CRASH = 5
    # CRASH_FATAL_EXCEPTION = 6
    # NEEDS_PRICE = 7
    # INVALID = 8
    # DID_NOT_OPEN = 9


    @staticmethod
    def default_dict():
        '''
            Default value for a report key.
        '''
        return  {
            'status': 1337,
            'name': "",
            'package_name': "",
            'report_title': "",
            'history': [],
            'app_info': {},
            'logs': '',
            'google_logged_in': '',  # Logged into app w/...
            'facebook_logged_in': '',  # Logged into app w/...
            'email_logged_in': '',  # Logged into app w/...
            'has_google': '',  # Found w/ detection
            'has_facebook': '',  # Found w/ detection
            'has_email': '',  # Found w/ detection
        }

    def __init__(self, device: Device):
        # Device and Session information for the report.
        self.__device = device.info
        self.__report_title = f'{self.__device.device_name}_{self.__device.ip}'
        self.__report = {self.__report_title: collections.defaultdict(ValidationReport.default_dict)}

    @property
    def report_title(self):
        return self.__report_title

    @property
    def report(self):
        return self.__report

    def add_app(self, package_name: str, app_name: str):
        ''' Adds an app to the report. '''
        if self.__report[self.__report_title][package_name]['status'] == 1337:
            self.__report[self.__report_title][package_name]['package_name'] = package_name
            self.__report[self.__report_title][package_name]['name'] = app_name
            self.__report[self.__report_title][package_name]['report_title'] = self.__report_title
            self.__report[self.__report_title][package_name]['status'] = AppStatus.INIT.value

    def update_app_info(self, package_name: str, info: AppData):
        self.__report[self.__report_title][package_name]['app_info'] = info

    def update_status(self, package_name: str, status: AppStatus):
        self.__report[self.__report_title][package_name]['status'] = status.value


    def update_status_login(self, package_name: str, login_results: AppLoginResults):
        ''' Updates app status to indicate if the app used a specificed login method or has a specific method. '''
        for key, val in login_results.__dict__.items():
            if val:
                self.__report[self.__report_title][package_name][key] = val

    def add_history(self, package_name: str, history_msg: str, driver: Remote):
        full_path = ''
        try:
            num = len(self.report[self.report_title][package_name]['history'])
            path = f"{get_root_path()}/images/history/{self.__device.ip}/{package_name}"
            create_dir_if_not_exists(path)
            full_path = f"{path}/{num}.png"
            driver.get_screenshot_as_file(full_path)
        except Exception as error:
            print("Error grabbing screenshot to update history.")
            pass

        self.__report[self.__report_title][package_name]['history'].append({"msg": history_msg, "img": full_path })


    def add_logs(self, package_name: str, logs: str):
        self.__report[self.__report_title][package_name]['logs'] = logs

    def get_status_obj_by_app(self, package_name: str):
        return self.__report[self.__report_title][package_name]

    def merge(self, oreport: 'ValidationReport'):
        ''' Merges on report title, used to merge pre-process Facebook login report. '''
        title_to_merge_on = self.__report_title
        self.__report[title_to_merge_on].update(deepcopy(oreport.report[title_to_merge_on]))

      ##  Reporting



    @staticmethod
    def ascii_starting(color=None):
        ''' Report decoration.'''

        p_green('''
              _  _     _  _     _  _     _____ _            _   _                         _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  /  ___| |          | | (_)                      _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| \ `--.| |___ _ _ __| |_ _ _ __   __ _          |_  __  _|_  __  _|_  __  _|
           _| || |_ _| || |_ _| || |_   `--. \ __/ _` | '__| __| | '_ \ / _` |          _| || |_ _| || |_ _| || |_
          |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |  | |_| | | | | (_| |  _ _ _  |_  __  _|_  __  _|_  __  _|
            |_||_|   |_||_|   |_||_|   \____/ \__\__,_|_|   \__|_|_| |_|\__, | (_|_|_)   |_||_|   |_||_|   |_||_|
                                                                         __/ |
                                                                        |___/
        ''')

    @staticmethod
    def anim_starting():
        ''' Report decoration.'''
        # print("\033[2J")  # clear the screen
        # print("\033[0;0H")  # move cursor to top-left corner
        ValidationReport.ascii_starting()

    @staticmethod
    def ascii_header():
        ''' Report decoration.'''

        p_green('''
              _  _     _  _     _  _    ______                      _       _  _     _  _     _  _
            _| || |_ _| || |_ _| || |_  | ___ \                    | |    _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |_/ /___ _ __   ___  _ __| |_  |_  __  _|_  __  _|_  __  _|
            _| || |_ _| || |_ _| || |_  |    // _ \ '_ \ / _ \| '__| __|  _| || |_ _| || |_ _| || |_
           |_  __  _|_  __  _|_  __  _| | |\ \  __/ |_) | (_) | |  | |_  |_  __  _|_  __  _|_  __  _|
             |_||_|   |_||_|   |_||_|   \_| \_\___| .__/ \___/|_|   \__|   |_||_|   |_||_|   |_||_|
                                                | |
                                                |_|
        ''')

    @staticmethod
    def ascii_footer():
        ''' Report decoration.'''
        p_green('''
               _  _     _  _     _  _     _   ___ _ _       _       _    _ _           _  _____     _  _     _  _     _  _
             _| || |_ _| || |_ _| || |_  | | / (_) | |     | |     | |  | | |         | ||____ |  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |/ / _| | |_   _| |__   | |  | | |__   __ _| |    / / |_  __  _|_  __  _|_  __  _|
             _| || |_ _| || |_ _| || |_  |    \| | | | | | | '_ \  | |/\| | '_ \ / _` | |    \ \  _| || |_ _| || |_ _| || |_
            |_  __  _|_  __  _|_  __  _| | |\  \ | | | |_| | | | | \  /\  / | | | (_| | |.___/ / |_  __  _|_  __  _|_  __  _|
              |_||_|   |_||_|   |_||_|   \_| \_/_|_|_|\__,_|_| |_|  \/  \/|_| |_|\__,_|_|\____/    |_||_|   |_||_|   |_||_|
        ''')

    @staticmethod
    def sorted_package_name(p: List):
        ''' Serializable method to use for sorting. Sorts by package_name '''
        return p[0]

    @staticmethod
    def sorted_app_name(p: List):
        ''' Serializable method to use for sorting. Sorts by app_name '''
        return p[1]['name']

    @staticmethod
    def sorted_device_name(p: List):
        ''' Serializable method to use for sorting. '''
        return p['report_title']

    @staticmethod
    def print_app_report(package_name: str, status_obj: Dict):
        if status_obj['status'] == 1337:
            return
        is_good = status_obj['status'] >= AppStatus.PASS.value
        p_blue(f"{status_obj['name']} ", end="")
        p_cyan(f"{package_name} ", end="")
        if is_good:
            p_green("PASSED", end="")
        else:
            p_red(f"FAILED", end="")

        p_purple(f" - [{status_obj['report_title']}]", end="\n")

        p_blue(status_obj['app_info'], end='\n')



        # Print Logged in status
        logged_in_msg = [
            "\t Logged in with: ",
            f"Google, " if status_obj['google_logged_in'] else "",
            f"Facebook, " if status_obj['facebook_logged_in'] else "",
            f"Email " if status_obj['email_logged_in'] else ""
        ]
        p_cyan("".join(logged_in_msg))

        log_in_methods = [
            "\t Detected log in methods: ",
            f"Google, " if status_obj['has_google'] else "",
            f"Facebook, " if status_obj['has_facebook'] else "",
            f"Email " if status_obj['has_email'] else "",
        ]
        p_purple("".join(log_in_methods))


        # Print History
        for hist in status_obj['history']:
            p_yellow("\t", hist['msg'])
            p_yellow("\t\t", f"Img: {hist['img']}")
        p_blue()

    @staticmethod
    def print_report(report: 'ValidationReport'):
        '''  Prints all apps from a single report. '''
        # Sorted by packge name
        ValidationReport.ascii_header()
        for package_name, status_obj in sorted(report.report[report.report_title].items(), key=ValidationReport.sorted_package_name):
            ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()

    def print(self):
        ''' Prints 'self' report.'''
        ValidationReport.print_report(self)

    def print_reports(reports: List['ValidationReport']):
        ''' Prints app reports from a list of ValidationReport.
            This results in each device's report being print one after the other.
            So apps will not be grouped together.
        '''
        ValidationReport.ascii_header()
        for report in reports:
            for package_name, status_obj in sorted(report.report[report.report_title].items(), key=ValidationReport.sorted_package_name):
                ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()

    @staticmethod
    def group_reports_by_app(reports: List['ValidationReport']) -> collections.defaultdict(list):
        all_reports = collections.defaultdict(list)
        for report_instance in reports:
            for package_name, status_obj in report_instance.report[report_instance.report_title].items():
                all_reports[package_name].append(status_obj)
                all_reports[package_name] = sorted(all_reports[package_name], key=ValidationReport.sorted_device_name)
        return all_reports

    @staticmethod
    def print_reports_by_app(reports: List['ValidationReport']):
        ''' Reorders the reports so that all apps are printed grouped together.

            Makes for better view in summary report, we can compare each app's final status.
        '''
        all_reports = ValidationReport.group_reports_by_app(reports)

        ValidationReport.ascii_header()
        for package_name, status_objs in sorted(all_reports.items(), key=ValidationReport.sorted_package_name):
            for status_obj in status_objs:
                ValidationReport.print_app_report(package_name, status_obj)
        ValidationReport.ascii_footer()

if __name__ == "__main__":
    pass