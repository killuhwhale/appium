from dataclasses import dataclass
from subprocess import Popen
import sys
from typing import List
from appium.webdriver.appium_service import AppiumService
from utils.logging_utils import logger
from utils.utils import BASE_PORT

@dataclass(frozen=True)
class AppiumServiceItem:
    ip: str
    port: int
    service: Popen

    # def __del__(self):
    #     self.service.stop()

class AppiumServiceManager:
    '''
      Given list of ips, create a list of objects to group ip, port number and service.

      Server(wd/hub/4723) -> driver(4723) -> ip/device1
      Server(wd/hub/4724) -> driver(4724) -> ip/device2
      Server(wd/hub/4725) -> driver(4725) -> ip/device3
    '''
    def __init__(self, ips: List[str]):
        self.__ips = ips
        self.__base_port = BASE_PORT
        self.services: List[AppiumServiceItem] = []

    def cleanup_services(self):
        ''' Starts and stops the service immediately.

        When the program is stopped without stopping the service, it can cause issues reconnecting on subsequent runs.
        This will start all services for each ip and stop it right away, cleaning up appium serverside, apparently.

        Trial and error...
        '''
        logger.print_log(f"starting services for {self.__ips=}")
        for i, ip in enumerate(self.__ips):
            try:
                port = self.__base_port + i
                logger.print_log(f"Starting service: {port=} for device at {ip=}")
                service = AppiumService()
                service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
                while not service.is_listening or not service.is_running:
                    print("Waiting for appium service to listen...")
                service.stop()
            except Exception as error:
                print("Error cleaning up server", str(error))
            sys.exit(1)

    def start_services(self):
        print(f"starting services for {self.__ips=} \n")
        for i, ip in enumerate(self.__ips):
            try:
                port = self.__base_port + i
                print(f"Starting service: {port=} for device at {ip=} \n")
                service = AppiumService()
                process = service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
                while not service.is_listening or not service.is_running:
                    print("Waiting for appium service to listen...")

                self.services.append(AppiumServiceItem(ip, port, process))
            except Exception as error:
                print("Error starting appium server", str(error))
                return False
        return True

    def stop(self):
        for service in self.services:
            try:
                print("deleting server: ", service.service)
                service.service.terminate()
            except Exception as e:
                print("AppiumServiceManager ", e)