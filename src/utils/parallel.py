from multiprocessing import Process, Queue


from playstore.playstore import AppValidator, ValidationReport
from launcher.launcher import Launcher
from time import sleep
# from utils.utils import android_des_caps
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.utils import PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, TOP_500_APPS, adb_connect, android_des_caps, find_transport_id


def validate_task(queue: Queue, packages: List[List[str]], ip: str):
    '''
        A single task to validate apps on a given device.
    '''
    res = adb_connect(ip)
    transport_id = find_transport_id(ip)
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
    
    validator = AppValidator(driver, packages, transport_id)
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

    def run(self):
        ValidationReport.anim_starting()
        self.start_runs()

        print("started running, waiting for drivers and validators")
        merged_reports = {}
        reports = 0
        while reports < len(self.ips)-1:
            # Check if there is a message in the queue
            if not self.queue.empty():
                report = self.queue.get()
                merged_reports.update(report)
                reports += 1
            sleep(1.2)
        
        # input("Finished running")
        ValidationReport.print_reports(merged_reports)
        
        
        
                
    def start_runs(self) -> List[webdriver.Remote]:
        num_packages_ea = len(self.packages) // len(self.ips)
        rem_packages = len(self.packages) % len(self.ips)
        # 1000 apps
        # 250 ea
        # 0, 1 ,2 ,3 
        print(num_packages_ea)
        for i, ip in enumerate(self.ips):
            start = i * num_packages_ea
            end = start + num_packages_ea
            packages_to_test = self.packages[start: end]
            # make sure
            # TODO() modify so that the last ip gets the remainder of the packages... (rem_packages)
            process = Process(target=validate_task, args=(self.queue, packages_to_test, ip ))
            # Start the process
            process.start()
            

           