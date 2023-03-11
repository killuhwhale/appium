import collections
from copy import deepcopy
from appium import webdriver
from collections import defaultdict
from multiprocessing import Process, Queue
from time import sleep
from typing import List
from utils.utils import (
    CONFIG, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, WEIGHTS, Device, android_des_caps)
from playstore.playstore import AppValidator, FacebookApp, ValidationReport
import signal
import sys


def validate_task(queue: Queue, packages: List[List[str]], ip: str, device: Device, instance_num: int):
    '''
        A single task to validate apps on a given device.
    '''
    if not device.is_connected:
        queue.put({})
        return

    print(f"Creating driver for isntance {instance_num}.....")
    driver = webdriver.Remote(
        "http://localhost:4723/wd/hub",
        android_des_caps(
            ip,
            PLAYSTORE_PACKAGE_NAME,
            PLAYSTORE_MAIN_ACT
        )
    )
    driver.implicitly_wait(5)
    driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)

    fb_handle = FacebookApp(driver, device, instance_num)
    fb_handle.install_and_login()

    validator = AppValidator(
        driver,
        packages,
        device,
        instance_num
    )
    validator.uninstall_multiple()
    validator.run()


    # Need to add the Facebook report...
    # - Write a merge method to update the inner dict on device key...
    validator.report.merge(fb_handle.validator.report)
    print("Putting validator")
    queue.put(AppValidatorPickle(validator))
    driver.quit()


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
        self.update_app_names = deepcopy(validator.update_app_names)
        self.bad_apps = deepcopy(validator.bad_apps)

class MultiprocessTaskRunner:
    '''
        Starts running valdiate_task on each device/ ip.
    '''
    def __init__(self, ips: List[str], packages: List[List[str]], ):
        self.queue = Queue()
        self.drivers: List[webdriver.Remote] = []
        self.valdiators: List[AppValidator] = []
        self.ips = ips
        self.packages = packages
        self.devices: List[Device] = []

        self.processes = []
        self.__all_reports: List[ValidationReport] = []
        self.packages_recvd = defaultdict(list)
        self.update_app_names = collections.defaultdict(str)  # Collects apps to update
        self.bad_apps = collections.defaultdict(str)  # Collects apps to be removed
        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, _signal, _frame):
        '''
            This function will be called when the user presses CTRL+C
        '''
        print("CTRL+C pressed. Exiting program.",  _signal, _frame)
        # self.report.print()
        # try:
        #     merged_reports = {}
        #     for driver, validator in zip(self.drivers, self.valdiators):
        #         merged_reports.update(validator.report.report)
        #         driver.quit()
        #     print("Merged reports", merged_reports)
        #     self.clear_processes()
        #     ValidationReport.print_report(merged_reports)
        # except Exception as err:
        #     print("Error: ", err)
        sys.exit(1)

    def run(self):
        '''
            Main method to start running ea task.
        '''
        ValidationReport.anim_starting()
        if CONFIG.multi_split_packages:
            self.start_runs_split()
        else:
            self.start_runs()

        print("started running, waiting for drivers and validators")

        validators = 0
        while validators < len(self.ips):
            # Check if there is a message in the queue
            if not self.queue.empty():

                validator: AppValidatorPickle = self.queue.get()
                self.__all_reports.append(validator.report)
                self.update_app_names.update(validator.update_app_names)
                self.bad_apps.update(validator.bad_apps)
                validators += 1
                print(f"Validators: {validators=}")
            sleep(1.2)


    def get_final_reports(self):
        return self.__all_reports

    def clear_processes(self):
        '''
            Terminates each process.
        '''
        for p in self.processes:
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
        print(BANNER)
        for d in self.devices:
            print(f'\t{d}\n')

    def start_runs(self) -> List[webdriver.Remote]:
        '''
            Starts ea process w/ all pacakages in list.
        '''
        for i, ip in enumerate(self.ips):
            device = Device(ip)
            self.devices.append(device)
            process = Process(target=validate_task, args=(self.queue, self.packages, ip, device, i))
            process.start()
            self.processes.append(process)

    def start_runs_split(self) -> List[webdriver.Remote]:
        '''
            Splits up the packages to each ea task and starts ea process.
        '''
        total_packages = len(self.packages)
        num_packages_ea = total_packages // len(self.ips)
        rem_packages = total_packages % len(self.ips)
        start = 0
        for i, ip in enumerate(self.ips):
            end = start + num_packages_ea
            if rem_packages > 0:
                end += 1
                packages_to_test = self.packages[start: end]
                rem_packages -= 1
            else:
                packages_to_test = self.packages[start: end]

            print(f"Gave {ip} start - end: {start} - {end}")
            self.packages_recvd[ip] = [start, end]
            start = end

            device = Device(ip)
            self.devices.append(device)
            process = Process(target=validate_task, args=(self.queue, packages_to_test, ip, device, i))
            process.start()
            self.processes.append(process)
