from collections import defaultdict
from multiprocessing import Process, Queue
import signal
import sys
from time import sleep


from typing import List
from appium import webdriver


from utils.utils import (
    PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT,
    adb_connect, android_des_caps, find_transport_id, get_arc_version)
from playstore.playstore import AppValidator, ValidationReport


def validate_task(queue: Queue, packages: List[List[str]], ip: str):
    '''
        A single task to validate apps on a given device.
    '''

    if not adb_connect(ip):
        driver.quit()
        queue.put({})
        return

    transport_id = find_transport_id(ip)
    version = get_arc_version(transport_id)

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
    validator = AppValidator(driver, packages, transport_id, version, ip)
    validator.uninstall_multiple()
    validator.run()
    print("Putting driver & valdiator")
    driver.quit()
    queue.put(validator.report.report)



class MultiprocessTaskRunner:
    '''
        Starts running valdiate_task on each device/ ip.
    '''
    def __init__(self, ips: List[str], packages: List[List[str]]):
        self.queue = Queue()
        self.drivers: List[webdriver.Remote] = []
        self.valdiators: List[AppValidator] = []
        self.ips = ips
        self.packages = packages
        self.processes = []
        self.packages_recvd = defaultdict(list)
        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, _signal, _frame):
        '''
            This function will be called when the user presses CTRL+C
        '''
        print("CTRL+C pressed. Exiting program.",  _signal, _frame)
        # self.report.print_report()
        try:
            merged_reports = {}
            for driver, validator in zip(self.drivers, self.valdiators):
                merged_reports.update(validator.report.report)
                driver.quit()
            print("Merged reports", merged_reports)
            self.clear_processes()
            ValidationReport.print_reports(merged_reports)
        except Exception as err:
            print("Error: ", err)
        sys.exit(1)

    def run(self):
        '''
            Main method to start running ea task.
        '''
        ValidationReport.anim_starting()
        self.start_runs()

        print("started running, waiting for drivers and validators")
        merged_reports = {}
        reports = 0
        while reports < len(self.ips):
            # Check if there is a message in the queue
            if not self.queue.empty():
                report = self.queue.get()
                merged_reports.update(report)
                reports += 1
            sleep(1.2)
        print("Reports recv'd: ", reports, len(self.ips))
        # input("Finished running")
        ValidationReport.print_reports(merged_reports)

    def clear_processes(self):
        '''
            Terminates each process.
        '''
        for p in self.processes:
            try:
                p.terminate()
            except Exception as err:
                print("Failed to terminate process", err)

    def start_runs(self) -> List[webdriver.Remote]:
        '''
            Splits up the packages to each ea task and starts ea process.
        '''
        total_packages = len(self.packages)
        num_packages_ea = total_packages // len(self.ips)
        rem_packages = total_packages % len(self.ips)
        start = 0
        for ip in self.ips:
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

            process = Process(target=validate_task, args=(self.queue, packages_to_test, ip ))
            process.start()
            self.processes.append(process)