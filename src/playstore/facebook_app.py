from multiprocessing import Queue
from time import sleep
import __main__
from appium import webdriver
from playstore.app_validator import AppValidator
from utils.app_utils import close_app
from utils.device_utils import Device
from utils.logging_utils import AppLogger, p_alert
from utils.utils import (CONFIG, FACEBOOK_APP_NAME, FACEBOOK_PACKAGE_NAME)


class FacebookApp:
    ''' Specific instance of AppValidator to install and login to facebook for
        further auth.

        This will be ran before the main valdiation process.
    '''
    def __init__(self, driver: webdriver.Remote, app_logger: AppLogger,  device: Device, instance_num: int, stats_queue: Queue):
        self.__app_name = FACEBOOK_APP_NAME
        self.__package_name = FACEBOOK_PACKAGE_NAME
        self.__device = device
        self.__validator = AppValidator(
            driver,
            [[self.__app_name, self.__package_name],],
            device,
            instance_num,
            Queue(),
            app_logger,
            stats_queue,

        )

    @property
    def validator(self):
        return self.__validator

    def install_and_login(self):
        ''' Runs app valdiator to install, launch and login to Facebook.
        '''
        if not CONFIG.login_facebook:
            p_alert(f"Skipping pre-process FB install {CONFIG.login_facebook=}")
            return
        self.__validator.uninstall_app(self.__package_name, force_rm=True)
        self.__validator.run()
        sleep(3)
        close_app(self.__package_name, self.__device.info.transport_id)

if __name__ == "__main__":
    pass