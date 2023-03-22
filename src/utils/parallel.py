from logging import Logger
from appium.webdriver.appium_service import AppiumService
import collections
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from appium import webdriver
from collections import defaultdict
from multiprocessing import Process, Queue
from time import sleep
from typing import Any, Dict, List
from utils.utils import (
    BASE_PORT, CONFIG, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT,
    AppListTSV, AppLogger, Device, StatsLogger, android_des_caps, p_alert, p_blue,
    p_cyan, p_purple, p_red, logger, users_home_dir)
from playstore.playstore import AppValidator, FacebookApp, ValidationReport
import signal
import sys


@dataclass(frozen=True)
class AppiumServiceItem:
    ip: str
    port: int
    service: AppiumService

    def __del__(self):
        self.service.stop()

class AppiumServiceManager:
    '''
      Given list of ips, create a list of objects to group ip, port number and service.

      Server(we/hub/4723) -> driver(4723) -> ip/device1
      Server(we/hub/4724) -> driver(4724) -> ip/device2
      Server(we/hub/4725) -> driver(4725) -> ip/device3
    '''
    def __init__(self, ips: List[str]):
        self.__ips = ips
        self.__base_port = BASE_PORT
        self.services: List[AppiumServiceItem] = []
        self.__start_services()

    def __start_services(self):
        print(f"starting services for {self.__ips=}")
        for i, ip in enumerate(self.__ips):
            try:
                port = self.__base_port + i + 1
                print(f"Starting service: {port=} for device at {ip=}")
                service = AppiumService()
                service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
                while not service.is_listening or not service.is_running:
                    print("Waiting for appium service to listen...")

                self.services.append(AppiumServiceItem(ip, port, service))
            except Exception as error:
                print("Error starting appium server", str(error))


def update_app_list(queue: Queue ):
    ''' Separate process that will update the main apps list.

    Updating invloves renaming misnamed pacakges and removing invalid packages.
    '''
    tsv = AppListTSV()
    while True:
        if not queue.empty():
            update_type, package_name, app_name = queue.get()
            if update_type == 'misnamed':
                tsv.update_list({package_name: app_name})
            elif update_type == 'invalid':
                tsv.export_bad_apps({package_name: app_name})
            elif (update_type, package_name, app_name) == (None, None, None):
                p_alert("Breaking from")
                break

def validate_task(queue: Queue, app_list_queue: Queue, app_logger: AppLogger, stats_queue: Queue, packages: List[List[str]], ip: str, device: Device, port: int):
    '''
        A single task to validate apps on a given device.
    '''
    if not device.is_connected:
        queue.put({})
        return


    print(f"Creating driver for isntance {port}.....")
    try:
        driver = webdriver.Remote(
            f"http://localhost:{port}/wd/hub",
            android_des_caps(
                ip,
                PLAYSTORE_PACKAGE_NAME,
                PLAYSTORE_MAIN_ACT
            )
        )
    except Exception as error:
        p_alert(f"Error w/ driver @ {ip} w/ {port=}: ", error)
        queue.put({})
        return

    driver.implicitly_wait(5)
    driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)

    fb_handle = FacebookApp(driver, app_logger,  device, port, stats_queue,)
    fb_handle.install_and_login()

    validator = AppValidator(
        driver,
        packages,
        device,
        port - BASE_PORT,
        app_list_queue,
        app_logger,
        stats_queue,
    )
    if not CONFIG.skip_pre_multi_uninstall:
        p_alert(f"Skipping pre uninstall {CONFIG.skip_pre_multi_uninstall=}")
        validator.uninstall_multiple()
    validator.run()


    validator.report.merge(fb_handle.validator.report)
    print("Putting validator")
    queue.put(AppValidatorPickle(validator))
    driver.quit()


class ValidationReportStats:
    ''' Given a list of reports, calculate stats section.
    '''


    def __init__(self, queue: Queue):
        self.__queue = queue
        self.process = None
        self.nested_dict = lambda: defaultdict(self.nested_dict)
        self.reports = self.nested_dict()


    @staticmethod
    def default_item():
        return {
            'total_apps': 0,
            'total_misnamed': 0,
            'total_invalid': 0,
            'total_failed': 0,
            'total_passed': 0,
        }


    def task(self, queue: Queue):
        nested_dict = lambda: defaultdict(nested_dict)
        reports = nested_dict()
        stats_by_device: Dict[Any] = collections.defaultdict(dict)
        stats: Dict = dict()
        logger = StatsLogger()
        p_alert("Started stats task")
        while True:
            if not queue.empty():
                # Given some updated report
                status_obj: ValidationReport.default_dict = queue.get()
                reports[status_obj['report_title']][status_obj['package_name']] = status_obj

                stats, stats_by_device = ValidationReportStats.calc(reports)
                current_stats = ValidationReportStats.get_stats(stats, stats_by_device)
                logger.log(current_stats)


    def start(self):
        self.process = Process(target=self.task, args=(self.__queue, ))
        self.process.start()

    def stop(self):
        self.process.terminate()

    @staticmethod
    def calc(all_reports: Dict):
        '''

            Args:
             - all_reports: Is a nested default dictionary, nested_dict = lambda: defaultdict(nested_dict).
        '''
        total_apps = 0
        all_misnamed = collections.defaultdict(str)
        total_misnamed = 0
        all_invalid = collections.defaultdict(str)
        total_invalid = 0
        total_failed = 0

        devices = collections.defaultdict(ValidationReportStats.default_item)

        for report_title, dreport in all_reports.items():
            for package_name, status_obj in dreport.items():
                total_apps += 1
                devices[report_title]['total_apps'] += 1

                if status_obj['new_name']:
                    all_misnamed[package_name] = status_obj['new_name']
                    devices[report_title]['total_misnamed'] += 1

                elif status_obj["invalid"]:
                    all_invalid[package_name] = status_obj['name']
                    devices[report_title]['total_invalid'] += 1

                if status_obj['status'] == ValidationReport.FAIL:
                    total_failed += 1
                    devices[report_title]['total_failed'] += 1

                devices[report_title]['total_passed'] = devices[report_title]['total_apps'] - devices[report_title]['total_failed']



        total_misnamed = len(all_misnamed.keys())
        total_invalid = len(all_invalid.keys())

        # self.stats_by_device = devices
        stats = ValidationReportStats.default_item()
        stats['total_apps'] =  total_apps
        stats['total_misnamed'] =  total_misnamed
        stats['total_invalid'] =  total_invalid
        stats['total_failed'] =  total_failed
        stats['total_passed'] =  total_apps - total_failed

        return stats, devices

    @staticmethod
    def get_stats(stats: Dict, stats_by_device: collections.defaultdict(Any)):
        '''
        self.stats_by_device=defaultdict({
            'helios_192.168.1.238:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            },
            'coachz_192.168.1.113:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            },
            'eve_192.168.1.125:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            }
        })

        self.stats={
            'total_apps': 9,
            'total_misnamed': 1,
            'total_invalid': 1,
            'total_failed': 6,
            'all_misnamed': defaultdict({
                'com.facebook.orca': 'Messenger'
            }),
            'all_invalid': defaultdict({
                'com.softinit.iquitos.whatswebscan': 'Whats Web Scan'
            })
        }

        '''
        S = []
        HEADER = """
          _  _     _  _     _  _     _____ _        _           _  _     _  _     _  _
        _| || |_ _| || |_ _| || |_  /  ___| |      | |        _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| \ `--.| |_ __ _| |_ ___  |_  __  _|_  __  _|_  __  _|
        _| || |_ _| || |_ _| || |_   `--. \ __/ _` | __/ __|  _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |_\__ \ |_  __  _|_  __  _|_  __  _|
         |_||_|   |_||_|   |_||_|   \____/ \__\__,_|\__|___/   |_||_|   |_||_|   |_||_|  """

        # S.append(f"{HEADER}\n\n")
        sorder = StatsLogger.stat_order()
        S.append("All devices")
        for key in sorder:
            val = stats[key]
            if isinstance(val, int):
                name = key.replace("_", " ").title()
                # Absoulte, if app failed due to these reasons, it failed on all devices
                # Reporting the count this way shows how many apps are misnamed, and the total count of apps misnamed of those tested.
                if key in ['total_misnamed', 'total_invalid']:
                    S.append(f"\t{val * len(stats_by_device.items())} ({val})")
                else:
                    S.append(f"\t{val}")

        S.append(f"\n")


        for device_name, stats in stats_by_device.items():
            S.append(f"{device_name}")
            for key in sorder:
                val = stats[key]
                name = key.replace("_", " ").title()
                S.append(f"\t{val}")
            S.append(f"\n")
        return ''.join(S)

    @staticmethod
    def print_stats(stats: Dict, stats_by_device: collections.defaultdict(Any)):
        '''
        self.stats_by_device=defaultdict({
            'helios_192.168.1.238:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            },
            'coachz_192.168.1.113:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            },
            'eve_192.168.1.125:5555': {
                'total_apps': 3, 'total_misnamed': 1, 'total_invalid': 1, 'total_failed': 2
            }
        })

        self.stats={
            'total_apps': 9,
            'total_misnamed': 1,
            'total_invalid': 1,
            'total_failed': 6,
            'all_misnamed': defaultdict({
                'com.facebook.orca': 'Messenger'
            }),
            'all_invalid': defaultdict({
                'com.softinit.iquitos.whatswebscan': 'Whats Web Scan'
            })
        }

        '''
        HEADER = """
          _  _     _  _     _  _     _____ _        _           _  _     _  _     _  _
        _| || |_ _| || |_ _| || |_  /  ___| |      | |        _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| \ `--.| |_ __ _| |_ ___  |_  __  _|_  __  _|_  __  _|
        _| || |_ _| || |_ _| || |_   `--. \ __/ _` | __/ __|  _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |_\__ \ |_  __  _|_  __  _|_  __  _|
         |_||_|   |_||_|   |_||_|   \____/ \__\__,_|\__|___/   |_||_|   |_||_|   |_||_|  """

        p_cyan(HEADER, "\n\n")
        for key, val in stats.items():
            if isinstance(val, int):
                name = key.replace("_", " ").title()
                # Absoulte, if app failed, it failed on all devices
                if key in ['total_misnamed', 'total_invalid']:
                    p_cyan(f"\t{name}: {val * len(stats_by_device.items())} ({val})")
                else:
                    p_cyan(f"\t{name}: {val}")
        p_cyan(f"\tTotal passed: {stats['total_apps'] - stats['total_failed']}")


        p_blue("\n\n\tStats by device\n")
        for device_name, stats in stats_by_device.items():
            p_purple(f"\t{device_name}")
            for key, val in stats.items():
                name = key.replace("_", " ").title()
                p_cyan(f"\t\t{name}: {val}")
            p_cyan(f"\t\tTotal passed: {stats['total_apps'] - stats['total_failed']}")


class ValidationReportPickle:
    ''' Bundles the information needed to pass through the queue.
     '''
    def __init__(self, report: ValidationReport):
        self.report_title = report.report_title
        self.report = report.report

class AppValidatorPickle:
    ''' Bundles the information needed to pass through the queue.

        ObjDetector uses yolo code and it has lambdas, cannot pickle entire class.

     '''
    def __init__(self, validator: AppValidator):
        self.report = deepcopy(ValidationReportPickle(validator.report))

class MultiprocessTaskRunner:
    '''
        Starts running valdiate_task on each device/ ip.
    '''
    def __init__(self, ips: List[str], packages: List[List[str]] ):
        self.__queue = Queue()
        self.__app_list_queue = Queue()
        self.__app_list_process = None
        self.__app_logger = AppLogger()
        self.__drivers: List[webdriver.Remote] = []
        # self.valdiators: List[AppValidator] = []
        self.__ips = ips
        self.__packages = packages
        self.__devices: List[Device] = []
        self.__reports: List[ValidationReport] = []
        self.__processes = []

        self.__stats_queue = Queue()
        self.__validation_report_stats = ValidationReportStats(self.__stats_queue)
        self.__packages_recvd = defaultdict(list)

        self.__appium_service_manager = AppiumServiceManager(ips)
        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, _signal, _frame):
        '''
            This function will be called when the user presses CTRL+C
        '''
        print("CTRL+C pressed. Exiting program.",  _signal, _frame)
        try:
            for driver in self.__drivers:
                driver.quit()
            self.__clear_processes()
        except Exception as err:
            print("Error: ", err)
        sys.exit(1)

    @property
    def reports(self):
        return self.__reports

    @property
    def reports_dict(self):
        return {report.report_title: report.report for report  in self.__reports}

    def __start_app_list_renaming_task(self):
        self.__app_list_process = Process(target=update_app_list, args=(self.__app_list_queue,))
        self.__app_list_process.start()

    def run(self):
        '''
            Main method to start running ea task.
        '''
        ValidationReport.anim_starting()
        self.__start_app_list_renaming_task()
        self.__validation_report_stats.start()

        if CONFIG.multi_split_packages:
            self.__start_runs_split()
        else:
            self.__start_runs()

        print("started running, waiting for drivers and validators")

        validators = 0
        while validators < len(self.__ips):
            # Check if there is a message in the queue
            if not self.__queue.empty():
                validator: AppValidatorPickle = self.__queue.get()
                if hasattr(validator, 'report'):
                    self.__reports.append(validator.report)

                validators += 1
                print(f"Validators: {validators=}")
            sleep(1.2)
        self.__app_list_process.terminate()
        self.__validation_report_stats.stop()
        print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

    def __clear_processes(self):
        '''
            Terminates each process.
        '''
        for p in self.__processes:
            try:
                p.terminate()
            except Exception as err:
                print("Failed to terminate process", err)

    def print_devices(self):
        BANNER = '''
          _  _     _  _     _  _    ______           _                   _  _     _  _     _  _
        _| || |_ _| || |_ _| || |_  |  _  \         (_)                _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| | | | |_____   ___  ___ ___  ___  |_  __  _|_  __  _|_  __  _|
        _| || |_ _| || |_ _| || |_  | | | / _ \ \ / / |/ __/ _ \/ __|  _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| | |/ /  __/\ V /| | (_|  __/\__ \ |_  __  _|_  __  _|_  __  _|
         |_||_|   |_||_|   |_||_|   |___/ \___| \_/ |_|\___\___||___/   |_||_|   |_||_|   |_||_|  \n\n\n'''
        logger.print_log(BANNER)
        for d in self.__devices:
            logger.print_log(f'\t{d}\n')


    def __start_process(self, ip, port_number, apps: List[List[str]]):

        device = Device(ip)
        self.__devices.append(device)
        process = Process(target=validate_task, args=(self.__queue, self.__app_list_queue, self.__app_logger, self.__stats_queue, apps, ip, device, port_number))
        process.start()
        self.__processes.append(process)

    def __start_runs(self) -> List[webdriver.Remote]:
        '''
            Starts ea process w/ all pacakages in list.
        '''


        # for i, ip in enumerate(self.__ips):
        for i, service_item in enumerate(self.__appium_service_manager.services):
            self.__start_process(service_item.ip, service_item.port, self.__packages)
            # device = Device(ip)
            # self.__devices.append(device)
            # process = Process(target=validate_task, args=(self.__queue, self.__packages, ip, device, i))
            # process.start()
            # self.__processes.append(process)

    def __start_runs_split(self) -> List[webdriver.Remote]:
        '''
            Splits up the packages to each ea task and starts ea process.
        '''
        logger.print_log(f"Spliting apps across devices. {CONFIG.multi_split_packages=}")
        total_packages = len(self.__packages)
        num_packages_ea = total_packages // len(self.__ips)
        rem_packages = total_packages % len(self.__ips)
        start = 0
        # for i, ip in enumerate(self.__ips):
        for i, service_item in enumerate(self.__appium_service_manager.services):
            end = start + num_packages_ea
            if rem_packages > 0:
                end += 1
                packages_to_test = self.__packages[start: end]
                rem_packages -= 1
            else:
                packages_to_test = self.__packages[start: end]

            print(f"Gave {service_item.ip} start - end: {start} - {end}")
            self.__packages_recvd[service_item.ip] = [start, end]
            start = end

            self.__start_process(service_item.ip, service_item.port, packages_to_test)

