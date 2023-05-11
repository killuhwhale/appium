

import logging
from typing import Dict
from utils.utils import create_file_if_not_exists, users_home_dir


class AppListTSV:
    ''' Tranformation layer between persisted storage of list to python list.

        Creates python list from a file is users home dir named self.__filename.

        This also cleans/ filters the list. It will update misnamed apps and remove invalid package names.
        We can replace this with another class to interact with another data storage.

        **App list file must not contain duplicate package names.
    '''

    def __init__(self):
        self.__app_list = list()
        self.__filename = "app_list.tsv" # This file should be place in the home dir on linux ~/
        # self.__filename = "app_list_demo.tsv" # This file should be place in the home dir on linux ~/
        self.__badfilename = "bad_app_list.tsv" # This will be created in the home dir ~/
        self.__all_bad_apps = dict()
        self.__home_dir = users_home_dir()
        self.__read_file()
        self.__read_bad_apps()

    def get_apps(self):
        ''' Returns 2D list of apps that will be tested. '''
        return self.__app_list

    def __read_file(self):
        with open(f"{self.__home_dir}/{self.__filename}", 'r' ) as f:
            [self.__app_list.append([w.strip() for w in line.split("\t")]) for line in f.readlines()]

    def __read_bad_apps(self):
        create_file_if_not_exists(f"{self.__home_dir}/{self.__badfilename}")
        with open(f"{self.__home_dir}/{self.__badfilename}", 'r' ) as f:
            bad_apps = {}
            for line in f.readlines():
                app_name, package_name = line.split("\t")
                bad_apps[package_name.replace("\n", "")] = app_name
            self.__all_bad_apps = bad_apps

    def __write_bad_apps(self):
        with open(f"{self.__home_dir}/{self.__badfilename}", 'w') as f:
            pass  # Clear contents

        with open(f"{self.__home_dir}/{self.__badfilename}", 'w') as f:
            for package_name, app_name  in self.__all_bad_apps.items():
                f.write(f"{app_name.strip()}\t{package_name.strip()}\n")

    def export_bad_apps(self, bad_apps: Dict):
        '''
            After test run is completed, updates instance app_list by removing apps that are also in @bad_apps and then writes entire list to file.

            Args:
                - bad_apps: List of apps that are deemed invalid during test run.
        '''
        # Rm bad apps from app_list
        updated_list = [[app_name, package_name] for app_name, package_name in self.__app_list if not package_name in bad_apps]
        # Update app_list
        if not len(self.__app_list) == len(updated_list):
            self.__app_list = updated_list
            # input("Writing new app_list w/out bad apps", updated_list)
            self.__write_file()
            # Update bad list
            self.__all_bad_apps.update(bad_apps)
            self.__write_bad_apps()


    def update_list(self, updated_names: Dict):
        '''  After test run is completed, updates instance app_list with new names and then writes entire list to file.

            Args:
            - updated_names: List of apps that are had mismatched names as compared to the Playstore via web.
        '''
        i = 0
        end  = len(self.__app_list)
        num_updated = 0
        while i < end:
            _app_name, package_name = self.__app_list[i]
            # print(f"{app_name} {package_name} {len(package_name)=} {package_name in updated_names}")
            if package_name in updated_names:
                print("b4 Alrerady updated...", self.__app_list[i])
                if self.__app_list[i][0] == updated_names[package_name]:
                    # Already updated by another process.
                    return
                self.__app_list[i][0] = updated_names[package_name]
                num_updated += 1
            i += 1

        if num_updated:
            self.__write_file()

    def __write_file(self):
        with open(f"{self.__home_dir}/{self.__filename}", 'w' ) as f:
            pass  # Clear contents

        with open(f"{self.__home_dir}/{self.__filename}", 'w' ) as f:
            [f.write(f"{app[0]}\t{app[1]}\n") for app in self.__app_list]

class AppLogger:
    ''' Logs passed/ failed apps to tsv 'live' instead of at the end of the program like __AppEventLogger.
    '''
    def __init__(self):
        self.__packages_logged = dict()
        filename_failed = f'{users_home_dir()}/failed_apps_live.tsv'
        filename_passed = f'{users_home_dir()}/passed_apps_live.tsv'
        logger_failed = logging.getLogger('failed_apps_live')
        logger_passed = logging.getLogger('passed_apps_live')
        logger_failed.setLevel(logging.DEBUG)
        logger_passed.setLevel(logging.DEBUG)
        header = f"Package\tName\tReport title\tBuild\tDate\tReason\tNew name\tInvalid\tHistory\tLogs\n"
        # Create a file handler for the logger
        with open(filename_failed, 'w') as f:
            f.write(header)

        with open(filename_passed, 'w') as f:
            f.write(header)

        file_handler_failed = logging.FileHandler(filename_failed)
        file_handler_failed.setLevel(logging.DEBUG)
        file_handler_passed = logging.FileHandler(filename_passed)
        file_handler_passed.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = logging.Formatter('%(message)s')
        file_handler_failed.setFormatter(formatter)
        file_handler_passed.setFormatter(formatter)

        # Add the file handler to the logger
        logger_failed.addHandler(file_handler_failed)
        logger_passed.addHandler(file_handler_passed)
        self.__logger_failed = logger_failed
        self.__logger_passed = logger_passed

    @property
    def logger_failed(self):
        return self.__logger_failed

    @property
    def logger_passed(self):
        return self.__logger_passed

    def log(self, *args, **kwargs):
        # args = status, package_name, name, report_title, reason, new_name, invalid, history, logs
        if not args[1] in self.__packages_logged:
            message = '\t'.join(map(str, args[1:])).strip()

            if args[0] == 0:
                self.logger_passed.info(message)
            elif args[0] == 1:
                self.logger_failed.info(message)
            self.__packages_logged[args[1]] = True  # track logged package_device

class StatsLogger:
    ''' Logs stats as each app is completed.  '''

    @staticmethod
    def stat_order():
        return  ['total_apps','total_misnamed','total_invalid','total_failed','total_passed']

    def __init__(self):
        self.filename = f'{users_home_dir()}/latest_stat_report.tsv'
        logger = logging.getLogger('latest_stat_report')
        logger.setLevel(logging.DEBUG)

        sorder = '\t'.join([f'{key.replace("_", " ").title()}' for key in StatsLogger.stat_order()])

        self.__header = f"Summary For\t{sorder}\n"
        # Create a file handler for the logger
        self.clear()
        file_handler = logging.FileHandler(self.filename)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)
        self.__logger = logger

    @property
    def logger(self):
        return self.__logger

    def clear(self):
        with open(self.filename, 'w') as f:
            f.write(self.__header)


    def log(self, *args, **kwargs):
        self.clear()
        message = ' '.join(map(str, args))
        self.__logger.info(message)

class __AppEventLogger:
    ''' Logs events and summary reporting (after completion) for the latest run into latest_report.txt '''
    def __init__(self):
        filename = f'{users_home_dir()}/latest_report.txt'
        logger = logging.getLogger('my_logger')
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        with open(filename, 'w'):
            pass

        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)
        self.logger = logger


    def log(self, *args, **kwargs):
        message = ' '.join(map(str, args)) + kwargs['end'] if 'end' in kwargs else '\n'
        self.logger.info(message)

    def print_log(self, *args, **kwargs):
        message = ' '.join(map(str, args))
        self.logger.info(message)
        print(message, end=kwargs['end'] if 'end' in kwargs else '\n')


logger = __AppEventLogger()

##     Colored printing     ##
def get_color_printer(n):
    if(n % 6 == 0):
        return p_red
    elif(n % 6 == 1):
        return p_green
    elif(n % 6 == 2):
        return p_yellow
    elif(n % 6 == 3):
        return p_blue
    elif(n % 6 == 4):
        return p_purple
    elif(n % 6 == 5):
        return p_cyan



Red = "\033[31m"
Black = "\033[30m"
Green = "\033[32m"
Yellow = "\033[33m"
Blue = "\033[34m"
Purple = "\033[35m"
Cyan = "\033[36m"
White = "\033[37m"
RESET = "\033[0m"

def p_red(*args, end='\n'):
    print(Red, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_green(*args, end='\n'):
    print(Green, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_yellow(*args, end='\n'):
    print(Yellow, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_blue(*args, end='\n'):
    print(Blue, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_purple(*args, end='\n'):
    print(Blue, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_cyan(*args, end='\n'):
    print(Cyan, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_alert(*args):
    art = r"""
          _ ._  _ , _ ._
        (_ ' ( `  )_  .__)
      ( (  (    )   `)  ) _)
     (__ (_   (_ . _) _) ,__)
         `~~`\ ' . /`~~`
              ;   ;
              /   \
_____________/_ __ \_____________"""
    p_red(art)
    p_blue(*args)
    print()
