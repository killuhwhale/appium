
from appium import webdriver
from collections import defaultdict
from multiprocessing import Process, Queue
from time import sleep
from typing import List
from playstore.app_validator import AppValidator
from playstore.facebook_app import FacebookApp
from playstore.validation_report import ValidationReport
from playstore.validation_report_stats import ValidationReportStats
from prices.prices import Prices
from serviceManager.appium_service_manager import AppiumServiceManager
from utils.device_utils import Device
from utils.logging_utils import AppListTSV, AppLogger, p_alert, logger
from utils.pickles import AppValidatorPickle

from utils.utils import (
    BASE_PORT, CONFIG, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT,
    android_des_caps, nested_default_dict)

import signal
import sys

def update_app_list(queue: Queue ):
    ''' Separate process that will update the main apps list.

    Updating invloves renaming misnamed pacakges and removing invalid packages.
    '''
    tsv = AppListTSV()
    print("Starting update app list process...")
    while True:
        if not queue.empty():
            print(f"Recv'd @ update_app_list")

            update_type, package_name, app_name = queue.get()
            if update_type == 'misnamed':
                tsv.update_list({package_name: app_name})
            elif update_type == 'invalid':
                tsv.export_bad_apps({package_name: app_name})
            elif (update_type, package_name, app_name) == (None, None, None):
                p_alert("Breaking from")
                break

def validate_task(queue: Queue, app_list_queue: Queue, app_logger: AppLogger, stats_queue: Queue, price_queue: Queue, packages: List[List[str]], ip: str, device: Device, port: int):
    '''
        A single task to validate apps on a given device.
    '''
    if not device.is_connected:
        print("device is not connected")
        queue.put({})
        return

    print(f"Creating driver for instance/port {port}.....")
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
        price_queue,
    )
    if not CONFIG.skip_pre_multi_uninstall:
        validator.uninstall_multiple()
    validator.run()

    validator.report.merge(fb_handle.validator.report)
    print("Putting validator")
    queue.put(AppValidatorPickle(validator))


class MultiprocessTaskRunner:
    '''
        Starts running valdiate_task on each device/ ip.
    '''
    def __init__(self, ips: List[str], packages: List[List[str]] ):
        self.__queue = Queue()
        self.__app_list_queue = Queue()
        self.__app_list_process = None
        self.__app_logger = AppLogger()

        self.__ips = ips
        self.__packages = packages
        self.__devices: List[Device] = []
        self.__reports: List[ValidationReport] = []
        self.__processes = []

        self.__stats_queue = Queue()
        self.__validation_report_stats = ValidationReportStats(self.__stats_queue)
        self.__packages_recvd = defaultdict(list)
        self.__price_queue = Queue()
        self.__prices = Prices(self.__price_queue)
        self.__appium_service_manager = AppiumServiceManager(ips)
        self.__appium_service_manager.start_services()
        signal.signal(signal.SIGINT, self.handle_sigint)



    def start_appium_server(self):
        return self.__appium_service_manager.start_services()

    def cleanup_appium_server(self):
        '''Will exit after running.'''
        self.__appium_service_manager.cleanup_services()

    def handle_sigint(self, _signal, _frame):
        '''
            This function will be called when the user presses CTRL+C
        '''
        print("CTRL+C pressed. Exiting program.",  _signal, _frame)
        try:
            self.__clear_processes()
        except Exception as err:
            print("Error: ", err)
        sys.exit(1)

    @property
    def reports(self):
        return self.__reports

    @property
    def reports_dict(self):
        reports = nested_default_dict()

        for report  in self.__reports:
            for package_name, status_obj in report.report[report.report_title].items():
                reports[status_obj['report_title']][status_obj['package_name']] = status_obj
        return reports

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
        self.__prices.start()

        if CONFIG.multi_split_packages:
            self.__start_runs_split()
        else:
            self.__start_runs()

        validators = 0
        while validators < len(self.__ips):
            # Check if there is a message in the queue
            if not self.__queue.empty():
                validator: AppValidatorPickle = self.__queue.get()
                if hasattr(validator, 'report'):
                    print(f"Recv'd validator: ", validator, validator.report)
                    self.__reports.append(validator.report)

                validators += 1
                print(f"Validators: {validators=}")
            sleep(1.2)
        self.__app_list_process.terminate()
        self.__validation_report_stats.stop()
        self.__prices.stop()
        self.__appium_service_manager.stop()
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
        try:
            device = Device(ip)
            dev_info = device.info
            self.__devices.append(device)
            process = Process(target=validate_task, args=(self.__queue, self.__app_list_queue, self.__app_logger, self.__stats_queue, self.__price_queue, apps, ip, device, port_number))
            process.start()
            self.__processes.append(process)
            logger.print_log(f"Started run on device: {dev_info=}", end="\n")
        except Exception as error:
            print("Error start process: ",  error)


    def __start_runs(self) -> List[webdriver.Remote]:
        '''
            Starts ea process w/ all pacakages in list.
        '''
        for i, service_item in enumerate(self.__appium_service_manager.services):
            self.__start_process(service_item.ip, service_item.port, self.__packages)

    def __start_runs_split(self) -> List[webdriver.Remote]:
        '''
            Splits up the packages to each ea task and starts ea process.
        '''
        logger.print_log(f"Spliting apps across devices. {CONFIG.multi_split_packages=}")
        total_packages = len(self.__packages)
        num_packages_ea = total_packages // len(self.__ips)
        rem_packages = total_packages % len(self.__ips)
        start = 0
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

