from typing import AnyStr, Dict
import os


def android_des_caps(device_name: AnyStr, app_package: AnyStr, main_activity: AnyStr) -> Dict:
    return {
        'platformName': 'Android',
        'appium:deviceName': device_name,
        'appium:appPackage': app_package,
        'appium:automationName': 'UiAutomator2',
        'appium:appActivity': main_activity,
        'appium:ensureWebviewHavepages': "true",
        'appium:nativeWebScreenshot': "true",
        'appium:newCommandTimeout': 3600,
        'appium:connectHardwareKeyboard': "true",
        'appium:noReset': "true",
    }


EXECUTOR = 'http://192.168.0.175:4723/wd/hub'
