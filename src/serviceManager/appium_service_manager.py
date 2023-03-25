from dataclasses import dataclass
import sys
from typing import List
from appium.webdriver.appium_service import AppiumService

from utils.utils import BASE_PORT

@dataclass(frozen=True)
class AppiumServiceItem:
    ip: str
    port: int
    service: AppiumService

    def __del__(self):
        try:
            self.service.stop()
        except:
            print("Cant stop wont stop.")

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

    def __del__(self):
        try:
            [s.service.stop() for s in self.services]
        except:
            pass


    def cleanup_services(self):
        ''' Starts and stops the service immediately.

        When the program is stopped without stopping the service, it can cause issues reconnecting on subsequent runs.
        This will start all services for each ip and stop it right away, cleaning up appium serverside, apparently.

        Trial and error...
        '''
        print(f"starting services for {self.__ips=}")
        for i, ip in enumerate(self.__ips):
            try:
                port = self.__base_port + i
                print(f"Starting service: {port=} for device at {ip=}")
                service = AppiumService()
                service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
                while not service.is_listening or not service.is_running:
                    print("Waiting for appium service to listen...")
                service.stop()
            except Exception as error:
                print("Error starting appium server", str(error))
            sys.exit(1)

    def start_services(self):
        print(f"starting services for {self.__ips=}")
        for i, ip in enumerate(self.__ips):
            try:
                port = self.__base_port + i
                print(f"Starting service: {port=} for device at {ip=}")
                service = AppiumService()
                service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
                while not service.is_listening or not service.is_running:
                    print("Waiting for appium service to listen...")

                self.services.append(AppiumServiceItem(ip, port, service))
            except Exception as error:
                print("Error starting appium server", str(error))
