from multiprocessing import Process, Queue
import signal
import sys


from playstore.playstore import AppValidator, ValidationReport
from time import sleep
# from utils.utils import android_des_caps
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.utils import ARC_VERSIONS, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, TOP_500_APPS, adb_connect, android_des_caps, find_transport_id, get_arc_version


def validate_task(queue: Queue, packages: List[List[str]], ip: str):
    '''
        A single task to validate apps on a given device.
    '''
    res = adb_connect(ip)
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
    
    validator = AppValidator(driver, packages, transport_id, version)
    validator.uninstall_multiple()
    validator.run()
    # validator.report.print_report()
    print("Putting driver & valdiator")
    driver.quit()
    queue.put(validator.report.report)
    
        




class MultiprocessTaskRunner:
    def __init__(self, ips: List[str], packages: List[List[str]]):
        # Create a queue for communication between the main process and the separate process
        self.queue = Queue()
        self.drivers: List[webdriver.Remote] = []
        self.valdiators: List[AppValidator] = []
        self.ips = ips
        self.packages = packages
        self.processes = []

        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, signal, frame):
        # This function will be called when the user presses CTRL+C
        print("CTRL+C pressed. Exiting program.")
        # self.report.print_report()
        try:
            merged_reports = {}
            for driver, validator in zip(self.drivers, self.valdiators):
                merged_reports.update(validator.report.report)
                # driver.quit()
            print("Merged reports", merged_reports)
            self.clear_processes()
            ValidationReport.print_reports(merged_reports)
        except Exception as e:
            pass
        sys.exit(1)

    


    def run(self):
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
        for p in self.processes:
            try:
                p.terminate() 
            except Exception as e:
                print("Failed to terminate process", e)
                
    def start_runs(self) -> List[webdriver.Remote]:
        total_packages = len(self.packages)
        num_packages_ea = total_packages // len(self.ips)
        rem_packages = total_packages % len(self.ips)
        # 1000 apps
        # 250 ea
        # 0, 1 ,2 ,3 
        print(num_packages_ea)
        start = 0
        for i, ip in enumerate(self.ips):            
            '''
                How to distribute remaining packages.
                    Image we have 10 ips and 999 packages to test
                    999 / 10 = 99
                    999 % 10 = 9
                    Then we know we can give 1 extra to each device. 
                        Only 1 device at the end will not reveice an extra package in this case.

                    0 -> 0 + 9 + 1
            '''
            end = start + num_packages_ea

            if rem_packages > 0:
                end += 1
                packages_to_test = self.packages[start: end]
                rem_packages -= 1
            else:
                packages_to_test = self.packages[start: end]
            
            start = end

            # make sure
            # TODO() modify so that the last ip gets the remainder of the packages... (rem_packages)
            
            
            process = Process(target=validate_task, args=(self.queue, packages_to_test, ip ))
            # Start the process
            process.start()
            self.processes.append(process)
            

           